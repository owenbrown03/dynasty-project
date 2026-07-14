from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.analytics.war.dynasty.factory import build_dynasty_war_service
from app.analytics.war.redraft.singleton import war_service
from app.analytics.war.redraft.service import WARSharedData
from app.crud.sleeper.draft import (
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
from app.services.draft.picks import (
    build_owned_pick_assets_by_roster_id,
    build_roster_name_by_id,
    get_first_future_pick_season,
)
from app.services.draft.projection import (
    build_draft_pick_projection_summary,
    build_projected_pick_slots_by_roster_id,
    build_projected_slot_source_label,
)
from app.services.draft.values import get_resolved_pick_values_by_key
from app.services.leagues.models import (
    LeagueDetailsResponse,
    LeagueOwner,
    LeaguePick,
    LeaguePlayer,
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
from app.services.waivers.dynasty import build_dynasty_projection

WAR_PLAYER_DISPLAY_LIMIT = 500
WAR_POSITION_RANK_DISPLAY_LIMIT = (
    WAR_PLAYER_DISPLAY_LIMIT // 4
)


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

        dynasty_service = build_dynasty_war_service()
        dynasty_war_by_player_id = {}

        for war_player in war_players:
            if war_player.player_id in dynasty_war_by_player_id:
                continue

            projection = build_dynasty_projection(
                player_war=war_player,
                dynasty_service=dynasty_service,
            )

            if projection is not None:
                dynasty_war_by_player_id[
                    war_player.player_id
                ] = projection

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
        traded_picks_by_league_id = await get_traded_picks_by_league_ids(
            db,
            [league_id],
        )
        projected_pick_slots_by_roster_id = (
            build_projected_pick_slots_by_roster_id(
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
            league
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

        rosters: list[LeagueRoster] = []

        for roster in roster_rows:
            roster_players = roster_players_by_roster_id.get(
                roster.roster_id,
                [],
            )

            picks = []
            total_pick_fc_value = 0.0
            total_pick_ktc_value = 0.0

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

                total_pick_fc_value += fc_value or 0.0
                total_pick_ktc_value += ktc_value or 0.0

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
                    total_moves=roster.total_moves,
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

        return LeagueDetailsResponse(
            league_id=league.league_id,
            league_name=league.name,
            avatar=league.avatar,
            season=str(league.season),
            total_rosters=league.total_rosters,
            roster_positions=list(
                league.roster_positions or [],
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
