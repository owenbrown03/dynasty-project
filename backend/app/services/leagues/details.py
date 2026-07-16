from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.analytics.war.redraft.singleton import war_service
from app.analytics.war.redraft.service import WARSharedData
from app.crud.sleeper.draft import (
    get_completed_draft_seasons_by_league_ids,
    get_drafts_by_league_ids,
    get_traded_picks_by_league_ids,
)
from app.crud.sleeper.league import (
    get_league_with_rosters,
    get_sync_states,
)
from app.crud.sleeper.personal import (
    get_user_notes_by_league_id,
)
from app.crud.sleeper.user import get_users
from app.crud.value import get_player_values
from app.models.db.fc.models import FantasyCalcValue
from app.models.db.sleeper import api as sleeper_model
from app.services.draft.picks import (
    build_owned_pick_assets_by_roster_id,
    build_roster_name_by_id,
    get_first_future_pick_season,
)
from app.services.draft.projection import (
    build_draft_pick_projection_summary,
    build_cached_projected_pick_slots_by_roster_id,
    build_projected_slot_source_label,
)
from app.services.draft.values import get_resolved_pick_values_by_key
from app.services.leagues.models import (
    LeagueDetailsResponse,
    LeagueOwner,
    LeaguePick,
    LeaguePlayer,
    LeagueRosterConstructionTarget,
    LeagueWarPlayerPoint,
    LeagueWarPlayerSeason,
    LeagueRoster,
    LeagueWarPositionSeason,
    LeagueWarPositionValue,
)
from app.services.leagues.settings import (
    build_settings_badges,
    build_settings_details,
)
from app.services.values.basis import ValueBasis
from app.services.personal_values import hydrate_personal_player_values
from app.services.war.shared import (
    build_cached_dynasty_projections_by_player_id,
    build_player_war_signature,
)

WAR_PLAYER_DISPLAY_LIMIT = 500
WAR_POSITION_RANK_DISPLAY_LIMIT = (
    WAR_PLAYER_DISPLAY_LIMIT // 4
)
ROSTER_CONSTRUCTION_HISTORY_YEARS = 5
ROSTER_CONSTRUCTION_POSITIONS = (
    "QB",
    "RB",
    "WR",
    "TE",
)
ROSTER_CONSTRUCTION_CACHE_TTL_SECONDS = (
    6 * 60 * 60
)
ROSTER_CONSTRUCTION_CACHE_VERSION = "v2"


def is_slot_eligible(slot: str, position: str | None) -> bool:
    if position is None:
        return False
    if slot in {"SUPER_FLEX", "OP"}:
        return position in {"QB", "RB", "WR", "TE"}
    if slot in {"FLEX", "REC_FLEX", "WRRB_FLEX"}:
        return position in {"RB", "WR", "TE"}
    if slot == "IDP_FLEX":
        return position in {"DL", "LB", "DB"}
    return position == slot


def calculate_projected_starter_points(
    *,
    roster_positions: list[str],
    players: list[LeaguePlayer],
) -> float:
    starters = [
        slot
        for slot in roster_positions
        if slot not in {"BN", "IR", "TAXI"}
    ]

    remaining = sorted(
        players,
        key=lambda player: (
            player.projected_points
            if player.projected_points is not None
            else float("-inf")
        ),
        reverse=True,
    )

    total = 0.0

    for slot in starters:
        match = next(
            (
                player
                for player in remaining
                if is_slot_eligible(
                    slot,
                    player.position,
                )
            ),
            None,
        )

        if match is None:
            continue

        remaining.remove(match)
        total += match.projected_points or 0.0

    return round(total, 2)


def calculate_average_age(
    players: list[LeaguePlayer],
) -> float | None:
    ages = [
        player.age
        for player in players
        if player.age is not None
    ]

    if not ages:
        return None

    return round(sum(ages) / len(ages), 1)


ROSTER_STAT_RANK_CONFIG = (
    ("projected_points", True),
    ("total_asset_ktc_value", True),
    ("total_asset_fc_value", True),
    ("total_ktc_value", True),
    ("total_pick_ktc_value", True),
    ("total_fc_value", True),
    ("total_pick_fc_value", True),
    ("total_pick_rookie_war_value", True),
    ("total_redraft_starter_war", True),
    ("total_redraft_roster_war", True),
    ("total_dynasty_starter_war", True),
    ("total_dynasty_roster_war", True),
    ("average_age", False),
    ("open_roster_spots", True),
    ("faab_remaining", True),
    ("waiver_position", False),
    ("total_trades", True),
)


def assign_roster_stat_ranks(
    rosters: list[LeagueRoster],
) -> None:
    for metric_name, descending in ROSTER_STAT_RANK_CONFIG:
        sorted_rosters = sorted(
            rosters,
            key=lambda roster: (
                (
                    getattr(
                        roster,
                        metric_name,
                        None,
                    )
                    is None
                ),
                (
                    -getattr(
                        roster,
                        metric_name,
                        0,
                    )
                    if descending
                    else getattr(
                        roster,
                        metric_name,
                        0,
                    )
                ),
                roster.roster_id,
            ),
        )

        previous_value = object()
        current_rank = 0

        for index, roster in enumerate(
            sorted_rosters,
            start=1,
        ):
            value = getattr(
                roster,
                metric_name,
                None,
            )

            if value != previous_value:
                current_rank = index
                previous_value = value

            roster.stat_ranks[metric_name] = current_rank


def build_direct_starter_minimums(
    roster_positions: list[str],
) -> dict[str, int]:
    return {
        position: sum(
            1
            for slot in roster_positions
            if slot == position
        )
        for position in ROSTER_CONSTRUCTION_POSITIONS
    }


def build_position_rank_war_history(
    seasonal_results: list[list],
) -> dict[str, dict[int, list[float]]]:
    history = {
        position: defaultdict(list)
        for position in ROSTER_CONSTRUCTION_POSITIONS
    }

    for results in seasonal_results:
        for position in ROSTER_CONSTRUCTION_POSITIONS:
            position_wars = sorted(
                (
                    getattr(
                        player,
                        "roster_war",
                        0.0,
                    ) or 0.0
                    for player in results
                    if player.position == position
                ),
                reverse=True,
            )

            for rank, war in enumerate(
                position_wars,
                start=1,
            ):
                history[position][rank].append(war)

    return history


def get_average_rank_war(
    *,
    history: dict[str, dict[int, list[float]]],
    position: str,
    rank: int,
) -> float:
    wars = history[position].get(rank)
    if wars:
        return sum(wars) / len(wars)

    return 0.0


def get_average_scarcity_band_war(
    *,
    history: dict[str, dict[int, list[float]]],
    position: str,
    per_team_slot: int,
    league_size: int,
) -> float:
    """
    Map a per-team roster slot to the correct league-wide scarcity band.

    Example in a 12-team league:
    - 1st rostered QB per team corresponds to QB1-QB12 league-wide
    - 2nd rostered QB per team corresponds to QB13-QB24
    - 3rd rostered QB per team corresponds to QB25-QB36

    Using the single positional rank directly (QB2, QB3, etc.) wildly
    overstates deep-position value and produces unrealistic targets like
    rostering 16 QBs per team.
    """

    safe_league_size = max(
        league_size,
        1,
    )
    safe_slot = max(
        per_team_slot,
        1,
    )
    band_start = (
        (safe_slot - 1) * safe_league_size
    ) + 1
    band_end = safe_slot * safe_league_size

    band_values = [
        get_average_rank_war(
            history=history,
            position=position,
            rank=rank,
        )
        for rank in range(
            band_start,
            band_end + 1,
        )
    ]
    populated_values = [
        value
        for value in band_values
        if value != 0.0
    ]

    if populated_values:
        return sum(populated_values) / len(
            populated_values,
        )

    return 0.0


def determine_target_roster_size(
    *,
    league,
    roster_rows: list,
) -> int:
    roster_sizes = [
        len(roster.players or [])
        + roster.open_roster_spots(league)
        for roster in roster_rows
    ]

    if not roster_sizes:
        return len(league.roster_positions or [])

    return max(roster_sizes)


async def get_trade_counts_by_roster_id(
    *,
    db: AsyncSession,
    league_id: str,
    roster_ids: list[int],
) -> dict[int, int]:
    if not roster_ids:
        return {}

    result = await db.execute(
        select(
            sleeper_model.Movement.roster_id,
            func.count(
                func.distinct(
                    sleeper_model.Transaction.transaction_id,
                )
            ),
        )
        .join(
            sleeper_model.Transaction,
            sleeper_model.Transaction.transaction_id
            == sleeper_model.Movement.transaction_id,
        )
        .where(
            sleeper_model.Transaction.league_id == league_id,
            sleeper_model.Transaction.type == "trade",
            sleeper_model.Movement.roster_id.in_(roster_ids),
        )
        .group_by(
            sleeper_model.Movement.roster_id,
        )
    )

    return {
        int(roster_id): int(trade_count)
        for roster_id, trade_count in result.all()
        if roster_id is not None
    }


def build_league_roster_construction_targets(
    *,
    league,
    roster_rows: list,
    seasonal_results: list[list],
) -> list[LeagueRosterConstructionTarget]:
    history = build_position_rank_war_history(
        seasonal_results,
    )
    direct_starter_minimums = build_direct_starter_minimums(
        list(league.roster_positions or []),
    )
    roster_size = determine_target_roster_size(
        league=league,
        roster_rows=roster_rows,
    )
    league_size = max(
        int(
            getattr(
                league,
                "total_rosters",
                0,
            )
            or 0
        ),
        len(roster_rows),
        1,
    )
    target_counts = dict(direct_starter_minimums)
    selected_war_by_position = {
        position: 0.0
        for position in ROSTER_CONSTRUCTION_POSITIONS
    }

    for position in ROSTER_CONSTRUCTION_POSITIONS:
        for rank in range(1, target_counts[position] + 1):
            selected_war_by_position[position] += (
                get_average_scarcity_band_war(
                    history=history,
                    position=position,
                    per_team_slot=rank,
                    league_size=league_size,
                )
            )

    while sum(target_counts.values()) < roster_size:
        next_position = max(
            ROSTER_CONSTRUCTION_POSITIONS,
            key=lambda position: (
                get_average_scarcity_band_war(
                    history=history,
                    position=position,
                    per_team_slot=(
                        target_counts[position] + 1
                    ),
                    league_size=league_size,
                ),
                -target_counts[position],
                -direct_starter_minimums[position],
                position,
            ),
        )
        next_rank = target_counts[next_position] + 1
        target_counts[next_position] = next_rank
        selected_war_by_position[next_position] += (
            get_average_scarcity_band_war(
                history=history,
                position=next_position,
                per_team_slot=next_rank,
                league_size=league_size,
            )
        )

    total_selected_war = sum(
        max(war, 0.0)
        for war in selected_war_by_position.values()
    )

    return [
        LeagueRosterConstructionTarget(
            position=position,
            target_count=target_counts[position],
            war_share=round(
                (
                    max(
                        selected_war_by_position[position],
                        0.0,
                    ) / total_selected_war
                ) * 100,
                1,
            ) if total_selected_war > 0 else 0.0,
        )
        for position in ROSTER_CONSTRUCTION_POSITIONS
    ]


def _build_roster_construction_cache_key(
    *,
    league,
    roster_rows: list,
    seasonal_results: list[list],
) -> str:
    digest = hashlib.sha256()
    digest.update(
        json.dumps(
            {
                "league_id": league.league_id,
                "season": league.season,
                "total_rosters": league.total_rosters,
                "roster_positions": (
                    league.roster_positions or []
                ),
                "roster_sizes": sorted(
                    [
                        len(roster.players or [])
                        + roster.open_roster_spots(
                            league,
                        )
                        for roster in roster_rows
                    ]
                ),
                "seasonal_signatures": [
                    build_player_war_signature(
                        player_wars=list(results),
                    )
                    for results in seasonal_results
                ],
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    return (
        "roster-construction:"
        f"{ROSTER_CONSTRUCTION_CACHE_VERSION}:"
        f"{digest.hexdigest()}"
    )


async def build_cached_league_roster_construction_targets(
    *,
    redis,
    league,
    roster_rows: list,
    seasonal_results: list[list],
) -> list[LeagueRosterConstructionTarget]:
    cache_key = _build_roster_construction_cache_key(
        league=league,
        roster_rows=roster_rows,
        seasonal_results=seasonal_results,
    )

    if redis is not None:
        cached_payload = await redis.get(
            cache_key,
        )

        if cached_payload:
            return [
                LeagueRosterConstructionTarget.model_validate(
                    row,
                )
                for row in json.loads(cached_payload)
            ]

    targets = build_league_roster_construction_targets(
        league=league,
        roster_rows=roster_rows,
        seasonal_results=seasonal_results,
    )

    if redis is not None:
        await redis.set(
            cache_key,
            json.dumps(
                [
                    target.model_dump()
                    for target in targets
                ],
                separators=(",", ":"),
            ),
            ttl_seconds=(
                ROSTER_CONSTRUCTION_CACHE_TTL_SECONDS
            ),
        )

    return targets


class LeagueDetails:
    def __init__(self):
        self.war_service = war_service

    async def get_league_details(
        self,
        db: AsyncSession,
        redis,
        league_id: str,
        site_user_id: UUID | None = None,
        draft_pick_projection_settings: dict[str, object] | None = None,
    ):
        leagues = await get_league_with_rosters(
            db,
            league_id,
        )

        if not leagues:
            return None

        league = leagues[0][0]
        roster_rows = [roster for _, roster in leagues]
        trade_counts_by_roster_id = (
            await get_trade_counts_by_roster_id(
                db=db,
                league_id=league_id,
                roster_ids=[
                    roster.roster_id
                    for roster in roster_rows
                ],
            )
        )
        notes_by_league_id = (
            await get_user_notes_by_league_id(
                db=db,
                site_user_id=site_user_id,
                league_ids=[league_id],
            )
            if site_user_id is not None
            else {}
        )
        sync_states = await get_sync_states(
            db,
            [league_id],
        )
        current_week = (
            sync_states[league_id].last_synced_week
            if league_id in sync_states
            else 0
        )

        shared = await self.war_service.load_shared_data(
            db,
            int(league.season),
        )
        roster_construction_seasonal_results = (
            await self.build_roster_construction_seasonal_results(
                db=db,
                league=league,
                players=shared.players,
                current_shared=shared,
            )
        )
        war_position_history = await self.build_war_position_history(
            db=db,
            league=league,
            players=shared.players,
            current_shared=shared,
        )
        war_player_history = await self.build_war_player_history(
            db=db,
            league=league,
            players=shared.players,
            current_shared=shared,
        )

        war_players = await self.war_service.calculate_with_data(
            league=league,
            shared=shared,
        )

        war_lookup = {
            player.player_id: player
            for player in war_players
        }

        dynasty_war_by_player_id = (
            await build_cached_dynasty_projections_by_player_id(
                redis=redis,
                player_wars=war_players,
            )
        )

        player_ids = set()
        owner_ids = set()

        for roster in roster_rows:
            player_ids.update(roster.players or [])
            if roster.owner_id:
                owner_ids.add(roster.owner_id)

        users = await get_users(
            db,
            owner_ids,
        )

        player_values = await get_player_values(
            db,
            player_ids,
            war_players,
            dynasty_war_by_player_id=dynasty_war_by_player_id,
        )
        player_values = await hydrate_personal_player_values(
            db=db,
            site_user_id=site_user_id,
            league=league,
            player_values=player_values,
            redis=redis,
        )

        player_map = {
            player.player_id: player
            for player in player_values
        }
        roster_players_by_roster_id: dict[
            int,
            list[LeaguePlayer],
        ] = {}
        projected_points_by_roster_id: dict[
            int,
            float,
        ] = {}

        num_qbs = (
            2
            if "SUPER_FLEX" in (league.roster_positions or [])
            else 1
        )
        ppr = int(
            round(
                float(
                    (league.scoring_settings or {}).get(
                        "rec",
                        1,
                    ) or 1
                )
            )
        )

        fantasycalc_rows = await db.execute(
            select(FantasyCalcValue).where(
                FantasyCalcValue.player_id.in_(player_ids),
                FantasyCalcValue.is_dynasty == True,
                FantasyCalcValue.num_qbs == num_qbs,
                FantasyCalcValue.num_teams == league.total_rosters,
                FantasyCalcValue.ppr == ppr,
            )
        )

        fantasycalc_by_player_id = {
            row.player_id: row
            for row in fantasycalc_rows.scalars().all()
        }

        for roster in roster_rows:
            starter_ids = set(roster.starters or [])

            starter_order = {
                player_id: index
                for index, player_id in enumerate(roster.starters or [])
            }

            roster_players: list[LeaguePlayer] = []

            for player_id in roster.players or []:
                player = player_map.get(player_id)
                if player is None:
                    continue

                fc_row = fantasycalc_by_player_id.get(player_id)

                roster_players.append(
                    LeaguePlayer(
                        player_id=player.player_id,
                        name=player.name,
                        position=player.position,
                        team=player.team,
                        age=player.age,
                        underdog_position_rank=player.underdog_position_rank,
                        projected_points=round(
                            war_lookup[player_id].projection,
                            2,
                        ) if player_id in war_lookup else None,
                        ktc_value=player.ktc_value,
                        fc_value=player.fc_value,
                        fc_trend_30_day=(
                            fc_row.trend_30_day
                            if fc_row is not None
                            else None
                        ),
                        redraft_starter_war=player.redraft_starter_war,
                        redraft_roster_war=player.redraft_roster_war,
                        dynasty_starter_war=player.dynasty_starter_war,
                        dynasty_roster_war=player.dynasty_roster_war,
                        my_redraft_starter_war=player.my_redraft_starter_war,
                        my_redraft_roster_war=player.my_redraft_roster_war,
                        my_dynasty_starter_war=player.my_dynasty_starter_war,
                        my_dynasty_roster_war=player.my_dynasty_roster_war,
                        is_starter=player_id in starter_ids,
                    )
                )

            roster_players.sort(
                key=lambda player: (
                    0 if player.is_starter else 1,
                    starter_order.get(player.player_id, 999),
                    -(
                        player.projected_points
                        if player.projected_points is not None
                        else -1
                    ),
                    player.name,
                ),
            )

            roster_players_by_roster_id[
                roster.roster_id
            ] = roster_players
            projected_points_by_roster_id[
                roster.roster_id
            ] = calculate_projected_starter_points(
                roster_positions=league.roster_positions or [],
                players=roster_players,
            )

        roster_name_by_id = build_roster_name_by_id(
            rosters=roster_rows,
            users_by_id=users,
        )
        redraft_starter_war_by_roster_id = {
            roster_id: round(
                sum(
                    player.redraft_starter_war or 0
                    for player in roster_players
                ),
                2,
            )
            for roster_id, roster_players in (
                roster_players_by_roster_id.items()
            )
        }
        redraft_roster_war_by_roster_id = {
            roster_id: round(
                sum(
                    player.redraft_roster_war or 0
                    for player in roster_players
                ),
                2,
            )
            for roster_id, roster_players in (
                roster_players_by_roster_id.items()
            )
        }

        drafts_by_league_id = await get_drafts_by_league_ids(
            db,
            [league_id],
        )
        completed_draft_seasons_by_league_id = (
            await get_completed_draft_seasons_by_league_ids(
                db,
                [league_id],
            )
        )
        traded_picks_by_league_id = await get_traded_picks_by_league_ids(
            db,
            [league_id],
        )
        projected_pick_slots_by_roster_id = (
            await build_cached_projected_pick_slots_by_roster_id(
                redis=redis,
                league=league,
                rosters=roster_rows,
                current_week=current_week,
                projected_points_by_roster_id=(
                    projected_points_by_roster_id
                ),
                redraft_starter_war_by_roster_id=(
                    redraft_starter_war_by_roster_id
                ),
                redraft_roster_war_by_roster_id=(
                    redraft_roster_war_by_roster_id
                ),
                settings=draft_pick_projection_settings,
            )
        )
        projected_pick_season = get_first_future_pick_season(
            league,
            drafts=drafts_by_league_id.get(league_id, []),
            completed_draft_seasons=(
                completed_draft_seasons_by_league_id.get(
                    league_id,
                    set(),
                )
            ),
        )
        projected_slots_by_season_and_roster_id = {
            (
                projected_pick_season,
                roster_id,
            ): slot
            for roster_id, slot in (
                projected_pick_slots_by_roster_id.slots_by_roster_id.items()
            )
        }
        projected_slot_source_label = (
            build_projected_slot_source_label(
                current_week=current_week,
                settings=draft_pick_projection_settings,
                method_used=(
                    projected_pick_slots_by_roster_id.method_used
                ),
                fallback_from_method=(
                    projected_pick_slots_by_roster_id.fallback_from_method
                ),
            )
            if projected_pick_slots_by_roster_id.slots_by_roster_id
            else None
        )

        raw_pick_assets_by_roster_id = build_owned_pick_assets_by_roster_id(
            league=league,
            rosters=roster_rows,
            drafts=drafts_by_league_id.get(league_id, []),
            traded_picks=traded_picks_by_league_id.get(league_id, []),
            roster_name_by_id=roster_name_by_id,
            projected_slots_by_season_and_roster_id=(
                projected_slots_by_season_and_roster_id
            ),
            projected_slot_source_label=(
                projected_slot_source_label
            ),
            completed_draft_seasons=(
                completed_draft_seasons_by_league_id.get(
                    league_id,
                    set(),
                )
            ),
        )

        all_pick_assets = [
            pick
            for picks in raw_pick_assets_by_roster_id.values()
            for pick in picks
        ]

        fc_pick_values_by_key = await get_resolved_pick_values_by_key(
            db,
            picks=all_pick_assets,
            value_basis=ValueBasis.FANTASYCALC,
            league_num_qbs=num_qbs,
            league_total_rosters=league.total_rosters,
            league_ppr=ppr,
        )

        ktc_pick_values_by_key = await get_resolved_pick_values_by_key(
            db,
            picks=all_pick_assets,
            value_basis=ValueBasis.KTC,
            league_num_qbs=num_qbs,
            league_total_rosters=league.total_rosters,
            league_ppr=ppr,
        )
        rookie_war_pick_values_by_key = await get_resolved_pick_values_by_key(
            db,
            picks=all_pick_assets,
            value_basis=ValueBasis.ROOKIE_PICK_WAR,
            league_num_qbs=num_qbs,
            league_total_rosters=league.total_rosters,
            league_ppr=ppr,
            league_scoring_settings=dict(
                league.scoring_settings or {},
            ),
            league_roster_positions=list(
                league.roster_positions or [],
            ),
        )

        rosters: list[LeagueRoster] = []

        for roster in roster_rows:
            roster_players = roster_players_by_roster_id.get(
                roster.roster_id,
                [],
            )

            picks = []
            total_pick_fc_value = 0.0
            total_pick_ktc_value = 0.0
            total_pick_rookie_war_value = 0.0

            for pick in raw_pick_assets_by_roster_id.get(
                roster.roster_id,
                [],
            ):
                key = (
                    pick.season,
                    pick.round,
                    pick.og_roster_id,
                )

                fc_pick_value = fc_pick_values_by_key.get(key)
                ktc_pick_value = ktc_pick_values_by_key.get(key)
                rookie_war_pick_value = (
                    rookie_war_pick_values_by_key.get(
                        key,
                    )
                )

                fc_value = (
                    fc_pick_value.value
                    if fc_pick_value is not None
                    else None
                )
                ktc_value = (
                    ktc_pick_value.value
                    if ktc_pick_value is not None
                    else None
                )
                rookie_war_value = (
                    rookie_war_pick_value.value
                    if rookie_war_pick_value is not None
                    else None
                )

                total_pick_fc_value += fc_value or 0.0
                total_pick_ktc_value += ktc_value or 0.0
                total_pick_rookie_war_value += (
                    rookie_war_value or 0.0
                )

                picks.append(
                    LeaguePick(
                        season=pick.season,
                        round=pick.round,
                        og_roster_id=pick.og_roster_id,
                        current_owner_roster_id=pick.current_owner_roster_id,
                        label=pick.label,
                        slot=pick.slot,
                        projected_slot=pick.projected_slot,
                        slot_source_label=pick.slot_source_label,
                        fc_value=fc_value,
                        ktc_value=ktc_value,
                        rookie_war_value=rookie_war_value,
                    )
                )

            total_ktc_value = round(
                sum(player.ktc_value or 0 for player in roster_players),
                2,
            )
            total_fc_value = round(
                sum(player.fc_value or 0 for player in roster_players),
                2,
            )
            total_redraft_starter_war = round(
                sum(player.redraft_starter_war or 0 for player in roster_players),
                2,
            )
            total_redraft_roster_war = round(
                sum(player.redraft_roster_war or 0 for player in roster_players),
                2,
            )
            total_dynasty_starter_war = round(
                sum(player.dynasty_starter_war or 0 for player in roster_players),
                2,
            )
            total_dynasty_roster_war = round(
                sum(player.dynasty_roster_war or 0 for player in roster_players),
                2,
            )

            owner = users.get(roster.owner_id) if roster.owner_id else None

            rosters.append(
                LeagueRoster(
                    roster_id=roster.roster_id,
                    owner=LeagueOwner(
                        user_id=owner.user_id if owner else None,
                        display_name=(
                            owner.display_name
                            if owner is not None
                            else f"Team {roster.roster_id}"
                        ),
                        avatar=owner.avatar if owner else None,
                    ),
                    rank=0,
                    record=f"{roster.wins}-{roster.losses}" + (
                        f"-{roster.ties}"
                        if roster.ties
                        else ""
                    ),
                    wins=roster.wins,
                    losses=roster.losses,
                    ties=roster.ties,
                    actual_points_for=round(roster.fpts, 2),
                    projected_points=projected_points_by_roster_id.get(
                        roster.roster_id,
                        0.0,
                    ),
                    faab_remaining=roster.faab_remaining(league),
                    waiver_position=roster.waiver_position,
                    total_trades=trade_counts_by_roster_id.get(
                        roster.roster_id,
                        0,
                    ),
                    open_roster_spots=roster.open_roster_spots(league),
                    average_age=calculate_average_age(roster_players),
                    total_ktc_value=total_ktc_value,
                    total_fc_value=total_fc_value,
                    total_redraft_starter_war=total_redraft_starter_war,
                    total_redraft_roster_war=total_redraft_roster_war,
                    total_dynasty_starter_war=total_dynasty_starter_war,
                    total_dynasty_roster_war=total_dynasty_roster_war,
                    total_pick_ktc_value=round(total_pick_ktc_value, 2),
                    total_pick_fc_value=round(total_pick_fc_value, 2),
                    total_pick_rookie_war_value=round(
                        total_pick_rookie_war_value,
                        2,
                    ),
                    total_asset_ktc_value=round(total_ktc_value + total_pick_ktc_value, 2),
                    total_asset_fc_value=round(total_fc_value + total_pick_fc_value, 2),
                    players=roster_players,
                    picks=sorted(
                        picks,
                        key=lambda pick: (
                            int(pick.season),
                            pick.round,
                            (
                                pick.slot
                                if pick.slot is not None
                                else (
                                    pick.projected_slot
                                    if pick.projected_slot is not None
                                    else 999
                                )
                            ),
                            pick.og_roster_id,
                        ),
                    ),
                )
            )

        rosters.sort(
            key=lambda roster: (
                roster.total_asset_ktc_value,
                roster.total_asset_fc_value,
                roster.total_dynasty_roster_war,
            ),
            reverse=True,
        )

        for rank, roster in enumerate(rosters, start=1):
            roster.rank = rank

        assign_roster_stat_ranks(
            rosters,
        )

        roster_construction_targets = (
            await build_cached_league_roster_construction_targets(
                redis=redis,
                league=league,
                roster_rows=roster_rows,
                seasonal_results=(
                    roster_construction_seasonal_results
                ),
            )
        )

        return LeagueDetailsResponse(
            league_id=league.league_id,
            league_name=league.name,
            avatar=league.avatar,
            season=str(league.season),
            total_rosters=league.total_rosters,
            roster_positions=list(
                league.roster_positions or [],
            ),
            roster_construction_targets=(
                roster_construction_targets
            ),
            draft_pick_projection_summary=(
                build_draft_pick_projection_summary(
                    current_week=current_week,
                    settings=draft_pick_projection_settings,
                    method_used=(
                        projected_pick_slots_by_roster_id.method_used
                    ),
                    fallback_from_method=(
                        projected_pick_slots_by_roster_id.fallback_from_method
                    ),
                )
                if projected_pick_slots_by_roster_id.slots_by_roster_id
                else None
            ),
            note=(
                notes_by_league_id[league_id].note
                if league_id in notes_by_league_id
                else ""
            ),
            settings_badges=build_settings_badges(league),
            settings_details=build_settings_details(league),
            war_position_history=war_position_history,
            war_player_history=war_player_history,
            rosters=rosters,
        )

    async def build_roster_construction_seasonal_results(
        self,
        *,
        db: AsyncSession,
        league,
        players: dict,
        current_shared: WARSharedData,
    ) -> list[list]:
        seasonal_results: list[list] = []
        current_season = int(league.season)

        for season in range(
            current_season - ROSTER_CONSTRUCTION_HISTORY_YEARS,
            current_season,
        ):
            stats_rows = await self.war_service.loader.get_season_stats(
                db,
                season,
            )

            if not stats_rows:
                continue

            season_league = league.model_copy(
                update={
                    "season": str(season),
                },
            )

            seasonal_results.append(
                await self.war_service.calculate_with_data(
                    league=season_league,
                    shared=WARSharedData(
                        players=players,
                        projections=stats_rows,
                    ),
                )
            )

        if seasonal_results:
            return seasonal_results

        return [
            await self.war_service.calculate_with_data(
                league=league,
                shared=current_shared,
            )
        ]

    async def build_war_position_history(
        self,
        *,
        db: AsyncSession,
        league,
        players: dict,
        current_shared: WARSharedData,
    ) -> list[LeagueWarPositionSeason]:
        seasons: list[LeagueWarPositionSeason] = []
        current_season = int(league.season)

        for season in range(current_season - 4, current_season):
            stats_rows = await self.war_service.loader.get_season_stats(
                db,
                season,
            )

            if not stats_rows:
                continue

            season_league = league.model_copy(
                update={
                    "season": str(season),
                },
            )

            results = await self.war_service.calculate_with_data(
                league=season_league,
                shared=WARSharedData(
                    players=players,
                    projections=stats_rows,
                ),
            )

            seasons.append(
                LeagueWarPositionSeason(
                    season=str(season),
                    source="historical",
                    values=self.aggregate_position_war(
                        results,
                    ),
                )
            )

        current_results = await self.war_service.calculate_with_data(
            league=league,
            shared=current_shared,
        )
        seasons.append(
            LeagueWarPositionSeason(
                season=str(current_season),
                source="projection",
                values=self.aggregate_position_war(
                    current_results,
                ),
            )
        )

        return seasons

    async def build_war_player_history(
        self,
        *,
        db: AsyncSession,
        league,
        players: dict,
        current_shared: WARSharedData,
    ) -> list[LeagueWarPlayerSeason]:
        seasons: list[LeagueWarPlayerSeason] = []
        current_season = int(league.season)
        war_types = [
            "starter",
            "roster",
        ]

        for season in range(current_season - 4, current_season):
            stats_rows = await self.war_service.loader.get_season_stats(
                db,
                season,
            )

            if not stats_rows:
                continue

            season_league = league.model_copy(
                update={
                    "season": str(season),
                },
            )

            results = await self.war_service.calculate_with_data(
                league=season_league,
                shared=WARSharedData(
                    players=players,
                    projections=stats_rows,
                ),
            )

            for war_type in war_types:
                seasons.append(
                    LeagueWarPlayerSeason(
                        season=str(season),
                        source="historical",
                        war_type=war_type,
                        players=self.build_position_rank_points(
                            results,
                            war_type=war_type,
                        ),
                    )
                )

        current_results = await self.war_service.calculate_with_data(
            league=league,
            shared=current_shared,
        )
        for war_type in war_types:
            seasons.append(
                LeagueWarPlayerSeason(
                    season=str(current_season),
                    source="projection",
                    war_type=war_type,
                    players=self.build_position_rank_points(
                        current_results,
                        war_type=war_type,
                    ),
                )
            )

        return seasons

    def aggregate_position_war(
        self,
        war_players,
    ) -> list[LeagueWarPositionValue]:
        positions = ["QB", "RB", "WR", "TE"]
        totals = {
            position: 0.0
            for position in positions
        }

        for player in war_players:
            if player.position not in totals:
                continue

            totals[player.position] += (
                player.roster_war or 0
            )

        return [
            LeagueWarPositionValue(
                position=position,
                war=round(totals[position], 2),
            )
            for position in positions
        ]

    def build_position_rank_points(
        self,
        war_players,
        *,
        war_type: str,
    ) -> list[LeagueWarPlayerPoint]:
        positions = ["QB", "RB", "WR", "TE"]
        points: list[LeagueWarPlayerPoint] = []
        war_attr = (
            "starter_war"
            if war_type == "starter"
            else "roster_war"
        )

        for position in positions:
            position_players = sorted(
                [
                    player
                    for player in war_players
                    if player.position == position
                    and getattr(player, war_attr) is not None
                ],
                key=lambda player: (
                    getattr(player, war_attr) or 0,
                    player.name,
                ),
                reverse=True,
            )

            for rank, player in enumerate(
                position_players[
                    :WAR_POSITION_RANK_DISPLAY_LIMIT
                ],
                start=1,
            ):
                points.append(
                    LeagueWarPlayerPoint(
                        player_id=player.player_id,
                        name=player.name,
                        position=position,
                        war=round(
                            getattr(player, war_attr) or 0,
                            2,
                        ),
                        rank=rank,
                    )
                )

        return points
