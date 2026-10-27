from __future__ import annotations

import hashlib
import json
import logging
from statistics import mean

logger = logging.getLogger(__name__)

from fastapi import HTTPException, Response, status
from sqlalchemy import select

from app.core.context import Context
from app.crud.auth.session import (
    get_session_draft_pick_projection_settings,
    get_session_finance_projection_settings,
)
from app.crud.auth.user import (
    get_draft_pick_projection_settings,
    get_finance_projection_settings,
)
from app.crud.sleeper.personal import (
    delete_finance_entry,
    get_commissioner_dues_by_key,
    get_finance_entries_by_key,
    get_finance_league_defaults_by_family_id,
    get_finance_user_defaults,
    get_hidden_league_ids,
    get_league_sort_orders,
    upsert_finance_entry,
    upsert_finance_league_default,
    upsert_finance_user_defaults,
)
from app.crud.sleeper.league import (
    get_playoff_matchups_by_league_ids,
    get_sync_states,
)
from app.crud.value import get_player_values
from app.analytics.war.redraft.singleton import war_service
from app.crud.sleeper.roster import get_owned_roster_rows
from app.schemas.finance import (
    FinanceDefaultSettings,
    FinanceLeagueDefaultEntry,
    FinanceLeagueDefaultsUpdate,
    FinanceLeagueSeasonEntry,
    FinanceLeagueSeasonUpdate,
    FinancePlacePayout,
    FinanceSeasonReset,
    FinanceSummaryResponse,
    FinanceDefaultsUpdate,
    FinanceTimelineResponse,
)
from app.models.db.sleeper.api import League, Roster
from app.models.db.auth import SiteUser
from app.services.draft.projection import (
    build_cached_projected_pick_slots_by_roster_id,
    build_redraft_value_by_roster_id,
    redraft_projection_basis_for_method,
    resolve_draft_pick_projection_method,
    resolve_finance_projection_settings,
)
from app.services.finance_math import (
    build_seed_finish_probabilities,
    calculate_expected_winnings_from_seed,
    calculate_projected_winnings,
    normalize_payout_structure,
    payout_for_rank,
    serialize_payout_structure,
)
from app.services.leagues.models import LeaguePlayer
from app.services.leagues.details import (
    calculate_projected_starter_points,
)
from app.services.war.shared import (
    build_league_war_fingerprint,
    build_shared_redraft_war_by_league_id,
)
from app.crud.sleeper.weekly_metrics import (
    get_league_weekly_metrics,
    sync_league_weekly_matchups,
)

FINANCE_PROJECTED_SEED_CACHE_TTL_SECONDS = (
    6 * 60 * 60
)
FINANCE_PROJECTED_SEED_CACHE_VERSION = "v1"
FINANCE_TIMELINE_CACHE_TTL_SECONDS = 300
FINANCE_TIMELINE_CACHE_VERSION = "v1"


def _require_finance_context(
    ctx: Context,
) -> None:
    if ctx.site_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    if ctx.connection is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Linked Sleeper account required",
        )


def calculate_rank(
    *,
    rosters: list[Roster],
    roster_id: int,
) -> int | None:
    ordered = sorted(
        rosters,
        key=lambda other: (
            other.wins,
            -other.losses,
            other.fpts,
            -other.roster_id,
        ),
        reverse=True,
    )
    return next(
        (
            index
            for index, other in enumerate(
                ordered,
                start=1,
            )
            if other.roster_id == roster_id
        ),
        None,
    )


async def get_rosters_by_league_id(
    *,
    ctx: Context,
    league_ids: list[str],
) -> dict[str, list[Roster]]:
    if not league_ids:
        return {}

    result = await ctx.db.execute(
        select(Roster).where(
            Roster.league_id.in_(league_ids),
        )
    )
    rosters_by_league_id: dict[str, list[Roster]] = {}

    for roster in result.scalars().all():
        rosters_by_league_id.setdefault(
            roster.league_id,
            [],
        ).append(roster)

    return rosters_by_league_id


def _build_finance_projected_seed_cache_key(
    *,
    ctx: Context,
    leagues_by_id: dict[str, League],
    rosters_by_league_id: dict[str, list[Roster]],
    effective_projection_settings: dict[str, object],
) -> str:
    digest = hashlib.sha256()
    digest.update(
        json.dumps(
            {
                "site_user_id": (
                    str(ctx.site_user.id)
                    if ctx.site_user is not None
                    else None
                ),
                "projection_settings": (
                    effective_projection_settings
                ),
                "leagues": {
                    league_id: {
                        "fingerprint": build_league_war_fingerprint(
                            league=league,
                        ),
                        "status": league.status,
                    }
                    for league_id, league in sorted(
                        leagues_by_id.items()
                    )
                },
                "rosters": {
                    league_id: [
                        {
                            "roster_id": roster.roster_id,
                            "wins": roster.wins,
                            "losses": roster.losses,
                            "ties": roster.ties,
                            "fpts": roster.fpts,
                            "ppts": roster.ppts,
                            "players": sorted(
                                roster.players or []
                            ),
                        }
                        for roster in sorted(
                            rosters,
                            key=lambda roster: (
                                roster.roster_id
                            ),
                        )
                    ]
                    for league_id, rosters in sorted(
                        rosters_by_league_id.items()
                    )
                },
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    return (
        "finance-projected-seeds:"
        f"{FINANCE_PROJECTED_SEED_CACHE_VERSION}:"
        f"{digest.hexdigest()}"
    )


def _build_finance_timeline_cache_key(
    *,
    ctx: Context,
    league_ids: list[str],
    season: str | None,
    current_week: int,
) -> str:
    digest = hashlib.sha256()
    digest.update(
        json.dumps(
            {
                "site_user_id": (
                    str(ctx.site_user.id)
                    if ctx.site_user is not None
                    else None
                ),
                "season": season,
                "current_week": current_week,
                "league_ids": sorted(league_ids),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    return (
        "finance-timeline:"
        f"{FINANCE_TIMELINE_CACHE_VERSION}:"
        f"{digest.hexdigest()}"
    )


async def build_finance_projected_seed_by_league_roster(
    *,
    ctx: Context,
    leagues_by_id: dict[str, League],
    rosters_by_league_id: dict[str, list[Roster]],
) -> dict[tuple[str, int], int]:
    draft_pick_projection_settings = (
        get_draft_pick_projection_settings(
            ctx.site_user,
        )
        if ctx.site_user is not None
        else get_session_draft_pick_projection_settings(
            ctx.session,
        )
    )
    finance_projection_settings = (
        get_finance_projection_settings(
            ctx.site_user,
        )
        if ctx.site_user is not None
        else get_session_finance_projection_settings(
            ctx.session,
        )
    )
    effective_projection_settings = (
        resolve_finance_projection_settings(
            finance_settings=finance_projection_settings,
            draft_pick_projection_settings=(
                draft_pick_projection_settings
            ),
            authenticated=ctx.site_user is not None,
        )
    )

    if effective_projection_settings["enabled"] is not True:
        return {}

    cache_key = _build_finance_projected_seed_cache_key(
        ctx=ctx,
        leagues_by_id=leagues_by_id,
        rosters_by_league_id=rosters_by_league_id,
        effective_projection_settings=(
            effective_projection_settings
        ),
    )

    if ctx.redis is not None:
        cached_payload = await ctx.redis.get(
            cache_key,
        )

        if cached_payload:
            return {
                (
                    league_id,
                    int(roster_id),
                ): projected_seed
                for league_id, roster_map in json.loads(
                    cached_payload,
                ).items()
                for roster_id, projected_seed in (
                    roster_map.items()
                )
            }

    sync_states = await get_sync_states(
        ctx.db,
        list(leagues_by_id.keys()),
    )
    projected_seed_by_key: dict[
        tuple[str, int],
        int,
    ] = {}

    all_metrics = await get_league_weekly_metrics(
        ctx.db,
        list(leagues_by_id.keys()),
    )
    latest_metrics_by_league: dict[str, dict[int, Any]] = {}
    if all_metrics:
        max_week_by_league: dict[str, int] = {}
        for m in all_metrics:
            if m.league_id not in max_week_by_league or m.week > max_week_by_league[m.league_id]:
                max_week_by_league[m.league_id] = m.week
        for m in all_metrics:
            if m.week == max_week_by_league.get(m.league_id):
                latest_metrics_by_league.setdefault(m.league_id, {})[m.roster_id] = m

    redraft_war_by_league_id: dict[str, list[PlayerWAR]] | None = None

    for league_id, league in leagues_by_id.items():
        rosters = rosters_by_league_id.get(
            league_id,
            [],
        )
        if not rosters:
            continue

        current_week = (
            sync_states[league_id].last_synced_week
            if league_id in sync_states
            else 0
        )

        league_metrics = latest_metrics_by_league.get(league_id, {})
        has_all_rosters_metrics = bool(rosters) and all(
            r.roster_id in league_metrics for r in rosters
        )

        if has_all_rosters_metrics:
            projected_points_by_roster_id = {
                r.roster_id: (league_metrics[r.roster_id].sleeper_projection or 0.0)
                for r in rosters
            }
            redraft_starter_war_by_roster_id = {
                r.roster_id: (league_metrics[r.roster_id].starter_war or 0.0)
                for r in rosters
            }
            redraft_roster_war_by_roster_id = {
                r.roster_id: (league_metrics[r.roster_id].roster_war or 0.0)
                for r in rosters
            }
            basis = (
                redraft_projection_basis_for_method(
                    resolve_draft_pick_projection_method(
                        current_week=current_week,
                        settings=effective_projection_settings,
                    )
                )
                or "sleeper_projection"
            )
            redraft_value_by_roster_id: dict[int, float] = {}
            for r in rosters:
                m = league_metrics[r.roster_id]
                if basis in {"fantasycalc", "fantasycalc_redraft"}:
                    val = m.fantasycalc_redraft or 0.0
                elif basis in {"ktc", "ktc_redraft"}:
                    val = m.ktc_redraft or 0.0
                elif basis == "redraft_starter_war":
                    val = m.starter_war or 0.0
                elif basis == "redraft_roster_war":
                    val = m.roster_war or 0.0
                else:
                    val = m.sleeper_projection or 0.0
                redraft_value_by_roster_id[r.roster_id] = val
        else:
            if redraft_war_by_league_id is None:
                redraft_war_by_league_id = (
                    await build_shared_redraft_war_by_league_id(
                        db=ctx.db,
                        redis=ctx.redis,
                        leagues=list(leagues_by_id.values()),
                        war_service=war_service,
                    )
                )
            redraft_war_players = redraft_war_by_league_id.get(league_id, [])
            war_lookup = {
                player.player_id: player
                for player in redraft_war_players
            }
            player_ids = [
                player_id
                for roster in rosters
                for player_id in (roster.players or [])
            ]
            player_values = await get_player_values(
                ctx.db,
                player_ids,
                redraft_war_players,
            )
            player_value_by_id = {
                player.player_id: player
                for player in player_values
            }

            projected_points_by_roster_id: dict[int, float] = {}
            redraft_starter_war_by_roster_id: dict[int, float] = {}
            redraft_roster_war_by_roster_id: dict[int, float] = {}

            for roster in rosters:
                roster_players: list[LeaguePlayer] = []

                for player_id in roster.players or []:
                    player_value = player_value_by_id.get(
                        player_id,
                    )
                    if player_value is None:
                        continue

                    roster_players.append(
                        LeaguePlayer(
                            player_id=player_value.player_id,
                            name=player_value.name,
                            position=player_value.position,
                            team=player_value.team,
                            projected_points=(
                                round(
                                    war_lookup[player_id].projection,
                                    2,
                                )
                                if player_id in war_lookup
                                else None
                            ),
                            redraft_starter_war=(
                                player_value.redraft_starter_war
                            ),
                            redraft_roster_war=(
                                player_value.redraft_roster_war
                            ),
                        )
                    )

                projected_points_by_roster_id[
                    roster.roster_id
                ] = calculate_projected_starter_points(
                    roster_positions=league.roster_positions or [],
                    players=roster_players,
                )
                redraft_starter_war_by_roster_id[
                    roster.roster_id
                ] = round(
                    sum(
                        player.redraft_starter_war or 0.0
                        for player in roster_players
                    ),
                    2,
                )
                redraft_roster_war_by_roster_id[
                    roster.roster_id
                ] = round(
                    sum(
                        player.redraft_roster_war or 0.0
                        for player in roster_players
                    ),
                    2,
                )

            redraft_value_by_roster_id = await build_redraft_value_by_roster_id(
                ctx.db,
                rosters,
                basis=(
                    redraft_projection_basis_for_method(
                        resolve_draft_pick_projection_method(
                            current_week=current_week,
                            settings=(
                                effective_projection_settings
                            ),
                        ),
                    )
                    or "sleeper_projection"
                ),
            )

        projection = await build_cached_projected_pick_slots_by_roster_id(
            redis=ctx.redis,
            league=league,
            rosters=rosters,
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
            redraft_value_by_roster_id=redraft_value_by_roster_id,
            settings=effective_projection_settings,
        )

        for roster_id, draft_slot in projection.slots_by_roster_id.items():
            projected_seed_by_key[
                (
                    league_id,
                    roster_id,
                )
            ] = max(
                1,
                league.total_rosters - draft_slot + 1,
            )

    if ctx.redis is not None:
        serialized = {}

        for (
            league_id,
            roster_id,
        ), projected_seed in projected_seed_by_key.items():
            serialized.setdefault(
                league_id,
                {},
            )[str(roster_id)] = projected_seed

        await ctx.redis.set(
            cache_key,
            json.dumps(
                serialized,
                separators=(",", ":"),
            ),
            ttl_seconds=(
                FINANCE_PROJECTED_SEED_CACHE_TTL_SECONDS
            ),
        )

    return projected_seed_by_key


def calculate_final_place_from_brackets(
    *,
    league_id: str,
    roster_id: int,
    playoff_matchups_by_league_id,
) -> int | None:
    matchups = playoff_matchups_by_league_id.get(
        league_id,
        [],
    )

    if not matchups:
        return None

    winners_participants = {
        roster_value
        for matchup in matchups
        if matchup.bracket_type == "winners"
        for roster_value in (
            matchup.team_one_roster_id,
            matchup.team_two_roster_id,
        )
        if roster_value is not None
    }

    winners_participant_count = len(
        winners_participants,
    )

    for matchup in matchups:
        if matchup.placement is None:
            continue

        placement_offset = (
            winners_participant_count
            if matchup.bracket_type == "losers"
            else 0
        )

        if matchup.winner_roster_id == roster_id:
            return placement_offset + matchup.placement

        if matchup.loser_roster_id == roster_id:
            return placement_offset + matchup.placement + 1

    return None


def _build_buy_in_by_league_season(
    dues_by_key,
) -> dict[tuple[str, str], float]:
    buy_in_by_league_season: dict[
        tuple[str, str],
        float,
    ] = {}

    for (
        league_id,
        _roster_id,
        season,
    ), record in dues_by_key.items():
        if record.buy_in_amount is None:
            continue

        buy_in_by_league_season[
            (
                league_id,
                season,
            )
        ] = record.buy_in_amount

    return buy_in_by_league_season


def _build_league_family_key_by_league_id(
    owned_rows,
) -> dict[str, str]:
    league_by_id = {
        league.league_id: league
        for _, league in owned_rows
    }
    family_key_by_league_id: dict[str, str] = {}

    for league_id, league in league_by_id.items():
        current = league
        visited: set[str] = set()

        while (
            current.previous_league_id
            and current.previous_league_id in league_by_id
            and current.previous_league_id not in visited
        ):
            visited.add(current.league_id)
            current = league_by_id[
                current.previous_league_id
            ]

        family_key_by_league_id[league_id] = current.league_id

    return family_key_by_league_id


def _build_family_name_by_league_id(
    owned_rows,
    family_key_by_league_id: dict[str, str],
) -> dict[str, str]:
    family_name_by_key: dict[str, tuple[int, str]] = {}

    for _, league in owned_rows:
        family_key = family_key_by_league_id.get(
            league.league_id,
            league.league_id,
        )
        season_value = int(league.season)
        previous = family_name_by_key.get(
            family_key,
        )

        if previous is None or season_value >= previous[0]:
            family_name_by_key[family_key] = (
                season_value,
                league.name,
            )

    return {
        family_key: league_name
        for family_key, (_, league_name) in family_name_by_key.items()
    }


def _serialize_default_settings(
    *,
    buy_in_amount: float | None,
    payout_structure: dict[str, float] | None,
) -> FinanceDefaultSettings:
    return FinanceDefaultSettings(
        buy_in_amount=(
            round(buy_in_amount, 2)
            if buy_in_amount is not None
            else None
        ),
        payout_structure=serialize_payout_structure(
            payout_structure,
        ),
    )


def _normalize_default_buy_in(
    buy_in_amount: float | None,
) -> float | None:
    if buy_in_amount is None:
        return None

    return round(
        float(buy_in_amount),
        2,
    )


def _normalize_default_payouts(
    payout_items: list[FinancePlacePayout],
) -> dict[str, float] | None:
    normalized = normalize_payout_structure(
        {
            str(item.place): item.amount
            for item in payout_items
        }
    )
    return normalized or None


def _resolve_entry_settings(
    *,
    finance_entry,
    league_default,
    user_defaults,
    commissioner_buy_in: float | None,
) -> dict[str, object]:
    if finance_entry is not None:
        return {
            "buy_in_amount": round(
                finance_entry.buy_in_amount,
                2,
            ),
            "buy_in_source": "season_override",
            "payout_structure": normalize_payout_structure(
                finance_entry.payout_structure,
            ),
            "payout_source": "season_override",
            "is_excluded": finance_entry.is_excluded,
            "has_season_override": True,
            "manual_winnings_amount": round(
                finance_entry.winnings_amount,
                2,
            ),
        }

    if (
        league_default is not None
        and league_default.buy_in_amount is not None
    ):
        buy_in_amount = round(
            league_default.buy_in_amount,
            2,
        )
        buy_in_source = "league_default"
    elif (
        user_defaults is not None
        and user_defaults.buy_in_amount is not None
    ):
        buy_in_amount = round(
            user_defaults.buy_in_amount,
            2,
        )
        buy_in_source = "global_default"
    elif commissioner_buy_in is not None:
        buy_in_amount = round(
            commissioner_buy_in,
            2,
        )
        buy_in_source = "commissioner_dues"
    else:
        buy_in_amount = 0.0
        buy_in_source = "none"

    if (
        league_default is not None
        and league_default.payout_structure is not None
    ):
        payout_structure = normalize_payout_structure(
            league_default.payout_structure,
        )
        payout_source = "league_default"
    elif (
        user_defaults is not None
        and user_defaults.payout_structure is not None
    ):
        payout_structure = normalize_payout_structure(
            user_defaults.payout_structure,
        )
        payout_source = "global_default"
    else:
        payout_structure = {}
        payout_source = "none"

    return {
        "buy_in_amount": buy_in_amount,
        "buy_in_source": buy_in_source,
        "payout_structure": payout_structure,
        "payout_source": payout_source,
        "is_excluded": False,
        "has_season_override": False,
        "manual_winnings_amount": 0.0,
    }


def _build_historical_payouts_by_family_and_rank(
    *,
    owned_rows,
    rosters_by_league_id,
    resolved_settings_by_key,
    family_key_by_league_id,
    playoff_matchups_by_league_id,
) -> dict[tuple[str, int], list[float]]:
    payouts_by_family_and_rank: dict[
        tuple[str, int],
        list[float],
    ] = {}

    for roster, league in owned_rows:
        key = (
            league.league_id,
            league.season,
        )
        resolved = resolved_settings_by_key[key]

        if resolved["is_excluded"]:
            continue

        rank = calculate_rank(
            rosters=rosters_by_league_id.get(
                league.league_id,
                [],
            ),
            roster_id=roster.roster_id,
        )
        finish_place = (
            calculate_final_place_from_brackets(
                league_id=league.league_id,
                roster_id=roster.roster_id,
                playoff_matchups_by_league_id=(
                    playoff_matchups_by_league_id
                ),
            )
            if league.status == "complete"
            else None
        )

        if finish_place is None:
            continue

        actual_winnings = payout_for_rank(
            resolved["payout_structure"],
            finish_place,
        )
        winnings_amount = round(
            (
                actual_winnings
                if actual_winnings is not None
                else resolved["manual_winnings_amount"]
            ),
            2,
        )

        if winnings_amount <= 0:
            continue

        payouts_by_family_and_rank.setdefault(
            (
                family_key_by_league_id[
                    league.league_id
                ],
                finish_place,
            ),
            [],
        ).append(
            winnings_amount,
        )

    return payouts_by_family_and_rank


async def get_finance_summary(
    ctx: Context,
) -> FinanceSummaryResponse:
    _require_finance_context(
        ctx,
    )

    raw_owned_rows = await get_owned_roster_rows(
        db=ctx.db,
        connection=ctx.connection,
    )
    hidden_league_ids = await get_hidden_league_ids(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
    )
    owned_rows = [
        (roster, league)
        for roster, league in raw_owned_rows
        if league.league_id not in hidden_league_ids
    ]

    sort_order = None

    if ctx.connection and ctx.connection.sleeper_user_id:
        sort_order = await get_league_sort_orders(
            db=ctx.db,
            user_id=ctx.connection.sleeper_user_id,
        )

    if sort_order:
        owned_rows.sort(
            key=lambda row: sort_order.get(
                row[1].league_id,
                9999,
            ),
        )

    league_ids = [
        league.league_id
        for _, league in owned_rows
    ]
    rosters_by_league_id = await get_rosters_by_league_id(
        ctx=ctx,
        league_ids=league_ids,
    )
    leagues_by_id = {
        league.league_id: league
        for _, league in owned_rows
    }
    projected_seed_by_league_roster = (
        await build_finance_projected_seed_by_league_roster(
            ctx=ctx,
            leagues_by_id=leagues_by_id,
            rosters_by_league_id=rosters_by_league_id,
        )
    )
    family_key_by_league_id = _build_league_family_key_by_league_id(
        owned_rows,
    )
    family_name_by_key = _build_family_name_by_league_id(
        owned_rows,
        family_key_by_league_id,
    )
    family_keys = list(
        family_name_by_key.keys(),
    )

    finance_entries_by_key = await get_finance_entries_by_key(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
        league_ids=league_ids,
    )
    playoff_matchups_by_league_id = (
        await get_playoff_matchups_by_league_ids(
            ctx.db,
            league_ids,
        )
    )
    user_defaults = await get_finance_user_defaults(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
    )
    league_defaults_by_family = (
        await get_finance_league_defaults_by_family_id(
            db=ctx.db,
            site_user_id=ctx.site_user.id,
            league_family_ids=family_keys,
        )
    )
    commissioner_dues_by_key = await get_commissioner_dues_by_key(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
        league_ids=league_ids,
    )
    commissioner_buy_in_by_league_season = (
        _build_buy_in_by_league_season(
            commissioner_dues_by_key,
        )
    )

    resolved_settings_by_key: dict[
        tuple[str, str],
        dict[str, object],
    ] = {}

    for _, league in owned_rows:
        key = (
            league.league_id,
            league.season,
        )
        family_key = family_key_by_league_id.get(
            league.league_id,
            league.league_id,
        )
        resolved_settings_by_key[key] = _resolve_entry_settings(
            finance_entry=finance_entries_by_key.get(
                key,
            ),
            league_default=league_defaults_by_family.get(
                family_key,
            ),
            user_defaults=user_defaults,
            commissioner_buy_in=(
                commissioner_buy_in_by_league_season.get(
                    key,
                )
            ),
        )

    historical_payouts_by_family_and_rank = (
        _build_historical_payouts_by_family_and_rank(
            owned_rows=owned_rows,
            rosters_by_league_id=rosters_by_league_id,
            resolved_settings_by_key=resolved_settings_by_key,
            family_key_by_league_id=family_key_by_league_id,
            playoff_matchups_by_league_id=(
                playoff_matchups_by_league_id
            ),
        )
    )

    entries: list[FinanceLeagueSeasonEntry] = []

    for roster, league in owned_rows:
        key = (
            league.league_id,
            league.season,
        )
        resolved = resolved_settings_by_key[key]
        family_key = family_key_by_league_id.get(
            league.league_id,
            league.league_id,
        )
        rank = (
            calculate_rank(
                rosters=rosters_by_league_id.get(
                    league.league_id,
                    [],
                ),
                roster_id=roster.roster_id,
            )
            if league.total_rosters > 0
            else None
        )
        finish_place = (
            calculate_final_place_from_brackets(
                league_id=league.league_id,
                roster_id=roster.roster_id,
                playoff_matchups_by_league_id=(
                    playoff_matchups_by_league_id
                ),
            )
            if league.status == "complete"
            else None
        )
        projected_finish_place = (
            projected_seed_by_league_roster.get(
                (
                    league.league_id,
                    roster.roster_id,
                )
            )
            if league.status in {"in_season", "post_season"}
            else finish_place
        )
        if (
            projected_finish_place is None
            and league.status == "complete"
        ):
            projected_finish_place = rank

        configured_winnings_amount = (
            payout_for_rank(
                resolved["payout_structure"],
                finish_place,
            )
            if finish_place is not None
            else None
        )
        winnings_amount = round(
            (
                configured_winnings_amount
                if configured_winnings_amount is not None
                else resolved["manual_winnings_amount"]
            ),
            2,
        )

        projected_winnings_source = "heuristic"
        historical_payouts = (
            historical_payouts_by_family_and_rank.get(
                (
                    family_key,
                    projected_finish_place,
                ),
                [],
            )
            if projected_finish_place is not None
            else []
        )

        projected_seed = (
            rank
            if league.status == "complete"
            else projected_finish_place
        )

        expected_winnings_amount = calculate_expected_winnings_from_seed(
            payout_structure=resolved["payout_structure"],
            projected_seed=projected_seed,
            total_rosters=league.total_rosters,
            playoff_teams=league.playoff_teams,
        )

        if expected_winnings_amount is not None:
            projected_winnings_amount = expected_winnings_amount
            projected_winnings_source = "seed_probability"
        elif (
            league.status in {"in_season", "post_season"}
            and projected_finish_place is None
        ):
            projected_winnings_amount = 0.0
            projected_winnings_source = "no_projection"
        elif configured_winnings_amount is not None:
            projected_winnings_amount = round(
                configured_winnings_amount,
                2,
            )
            projected_winnings_source = "configured_place"
        elif historical_payouts:
            projected_winnings_amount = round(
                mean(historical_payouts),
                2,
            )
            projected_winnings_source = "historical_rank"
        else:
            projected_winnings_amount = calculate_projected_winnings(
                buy_in_amount=resolved["buy_in_amount"],
                total_rosters=league.total_rosters,
                playoff_teams=league.playoff_teams,
                rank=projected_finish_place,
            )

        entries.append(
            FinanceLeagueSeasonEntry(
                league_id=league.league_id,
                league_family_id=family_key,
                league_name=league.name,
                season=league.season,
                status=league.status,
                total_rosters=league.total_rosters,
                rank=rank,
                finish_place=finish_place,
                projected_finish_place=projected_finish_place,
                wins=roster.wins,
                losses=roster.losses,
                points_for=round(roster.fpts, 2),
                buy_in_amount=round(
                    resolved["buy_in_amount"],
                    2,
                ),
                winnings_amount=winnings_amount,
                payout_structure=serialize_payout_structure(
                    resolved["payout_structure"],
                ),
                buy_in_source=resolved["buy_in_source"],
                payout_source=resolved["payout_source"],
                has_season_override=resolved["has_season_override"],
                has_league_default=family_key in league_defaults_by_family,
                is_excluded=resolved["is_excluded"],
                projected_winnings_amount=projected_winnings_amount,
                projected_winnings_source=projected_winnings_source,
                net_amount=round(
                    winnings_amount - resolved["buy_in_amount"],
                    2,
                ),
            )
        )

    entries.sort(
        key=lambda entry: (
            int(entry.season),
            entry.league_name.lower(),
        ),
        reverse=True,
    )

    included_entries = [
        entry
        for entry in entries
        if not entry.is_excluded
    ]

    league_defaults = [
        FinanceLeagueDefaultEntry(
            league_family_id=family_key,
            league_name=family_name_by_key.get(
                family_key,
                family_key,
            ),
            buy_in_amount=(
                round(default.buy_in_amount, 2)
                if default.buy_in_amount is not None
                else None
            ),
            payout_structure=serialize_payout_structure(
                default.payout_structure,
            ),
        )
        for family_key, default in sorted(
            league_defaults_by_family.items(),
            key=lambda item: (
                sort_order.get(item[0], 9999)
                if sort_order
                else 9999
            ),
        )
    ]

    return FinanceSummaryResponse(
        total_buy_ins=round(
            sum(entry.buy_in_amount for entry in included_entries),
            2,
        ),
        total_winnings=round(
            sum(entry.winnings_amount for entry in included_entries),
            2,
        ),
        total_net=round(
            sum(entry.net_amount for entry in included_entries),
            2,
        ),
        projected_current_winnings=round(
            sum(
                entry.projected_winnings_amount
                for entry in included_entries
            ),
            2,
        ),
        defaults=_serialize_default_settings(
            buy_in_amount=(
                user_defaults.buy_in_amount
                if user_defaults is not None
                else None
            ),
            payout_structure=(
                user_defaults.payout_structure
                if user_defaults is not None
                else None
            ),
        ),
        league_defaults=league_defaults,
        seasons=entries,
    )


async def build_dashboard_finance_metrics_by_league_id(
    *,
    db,
    redis,
    site_user_id,
    owned_rows: list[tuple[Roster, League]],
) -> dict[str, dict[str, float | int | None]]:
    """
    Builds lightweight current-season finance metrics for dashboard cards.

    This intentionally reuses the same projection and payout resolution
    rules as the finance tracker so the dashboard stays numerically
    consistent with the dedicated finance page.
    """

    if site_user_id is None or not owned_rows:
        return {}

    site_user = await db.get(
        SiteUser,
        site_user_id,
    )

    if site_user is None:
        return {}

    leagues_by_id = {
        league.league_id: league
        for _, league in owned_rows
    }
    league_ids = list(
        leagues_by_id.keys(),
    )

    ctx = Context(
        response=Response(),
        db=db,
        session=None,
        site_user=site_user,
        connection=None,
        sleeper=None,
        underdog=None,
        ktc=None,
        fc=None,
        gemini=None,
        redis=redis,
    )

    rosters_by_league_id = await get_rosters_by_league_id(
        ctx=ctx,
        league_ids=league_ids,
    )
    projected_seed_by_league_roster = (
        await build_finance_projected_seed_by_league_roster(
            ctx=ctx,
            leagues_by_id=leagues_by_id,
            rosters_by_league_id=rosters_by_league_id,
        )
    )
    family_key_by_league_id = _build_league_family_key_by_league_id(
        owned_rows,
    )
    finance_entries_by_key = await get_finance_entries_by_key(
        db=db,
        site_user_id=site_user.id,
        league_ids=league_ids,
    )
    playoff_matchups_by_league_id = (
        await get_playoff_matchups_by_league_ids(
            db,
            league_ids,
        )
    )
    user_defaults = await get_finance_user_defaults(
        db=db,
        site_user_id=site_user.id,
    )
    league_defaults_by_family = (
        await get_finance_league_defaults_by_family_id(
            db=db,
            site_user_id=site_user.id,
            league_family_ids=list(
                set(
                    family_key_by_league_id.values()
                )
            ),
        )
    )
    commissioner_dues_by_key = await get_commissioner_dues_by_key(
        db=db,
        site_user_id=site_user.id,
        league_ids=league_ids,
    )
    commissioner_buy_in_by_league_season = (
        _build_buy_in_by_league_season(
            commissioner_dues_by_key,
        )
    )

    resolved_settings_by_key: dict[
        tuple[str, str],
        dict[str, object],
    ] = {}

    for _, league in owned_rows:
        key = (
            league.league_id,
            league.season,
        )
        family_key = family_key_by_league_id.get(
            league.league_id,
            league.league_id,
        )
        resolved_settings_by_key[key] = _resolve_entry_settings(
            finance_entry=finance_entries_by_key.get(
                key,
            ),
            league_default=league_defaults_by_family.get(
                family_key,
            ),
            user_defaults=user_defaults,
            commissioner_buy_in=(
                commissioner_buy_in_by_league_season.get(
                    key,
                )
            ),
        )

    historical_payouts_by_family_and_rank = (
        _build_historical_payouts_by_family_and_rank(
            owned_rows=owned_rows,
            rosters_by_league_id=rosters_by_league_id,
            resolved_settings_by_key=resolved_settings_by_key,
            family_key_by_league_id=family_key_by_league_id,
            playoff_matchups_by_league_id=(
                playoff_matchups_by_league_id
            ),
        )
    )

    metrics_by_league_id: dict[
        str,
        dict[str, float | int | None],
    ] = {}

    for roster, league in owned_rows:
        key = (
            league.league_id,
            league.season,
        )
        resolved = resolved_settings_by_key[key]
        family_key = family_key_by_league_id.get(
            league.league_id,
            league.league_id,
        )
        rank = (
            calculate_rank(
                rosters=rosters_by_league_id.get(
                    league.league_id,
                    [],
                ),
                roster_id=roster.roster_id,
            )
            if league.total_rosters > 0
            else None
        )
        finish_place = (
            calculate_final_place_from_brackets(
                league_id=league.league_id,
                roster_id=roster.roster_id,
                playoff_matchups_by_league_id=(
                    playoff_matchups_by_league_id
                ),
            )
            if league.status == "complete"
            else None
        )
        projected_finish_place = (
            projected_seed_by_league_roster.get(
                (
                    league.league_id,
                    roster.roster_id,
                )
            )
            if league.status in {"in_season", "post_season"}
            else finish_place
        )
        if (
            projected_finish_place is None
            and league.status == "complete"
        ):
            projected_finish_place = rank

        configured_winnings_amount = (
            payout_for_rank(
                resolved["payout_structure"],
                finish_place,
            )
            if finish_place is not None
            else None
        )
        historical_payouts = (
            historical_payouts_by_family_and_rank.get(
                (
                    family_key,
                    projected_finish_place,
                ),
                [],
            )
            if projected_finish_place is not None
            else []
        )

        projected_seed = (
            rank
            if league.status == "complete"
            else projected_finish_place
        )

        expected_winnings_amount = calculate_expected_winnings_from_seed(
            payout_structure=resolved["payout_structure"],
            projected_seed=projected_seed,
            total_rosters=league.total_rosters,
            playoff_teams=league.playoff_teams,
        )

        if expected_winnings_amount is not None:
            projected_winnings_amount = expected_winnings_amount
        elif (
            league.status in {"in_season", "post_season"}
            and projected_finish_place is None
        ):
            projected_winnings_amount = 0.0
        elif configured_winnings_amount is not None:
            projected_winnings_amount = round(
                configured_winnings_amount,
                2,
            )
        elif historical_payouts:
            projected_winnings_amount = round(
                mean(historical_payouts),
                2,
            )
        else:
            projected_winnings_amount = calculate_projected_winnings(
                buy_in_amount=resolved["buy_in_amount"],
                total_rosters=league.total_rosters,
                playoff_teams=league.playoff_teams,
                rank=projected_finish_place,
            )


        metrics_by_league_id[league.league_id] = {
            "projected_payout": round(
                projected_winnings_amount,
                2,
            ),
            "projected_seed": projected_finish_place,
            "buy_in_amount": round(
                resolved["buy_in_amount"],
                2,
            ),
        }

    return metrics_by_league_id


async def save_finance_entry(
    body: FinanceLeagueSeasonUpdate,
    ctx: Context,
) -> FinanceLeagueSeasonEntry:
    _require_finance_context(
        ctx,
    )

    summary = await get_finance_summary(
        ctx,
    )
    existing = next(
        (
            entry
            for entry in summary.seasons
            if entry.league_id == body.league_id
            and entry.season == body.season
        ),
        None,
    )

    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League season not available in finance tracker",
        )

    await upsert_finance_entry(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
        league_id=body.league_id,
        season=body.season,
        buy_in_amount=body.buy_in_amount,
        winnings_amount=0.0,
        payout_structure=normalize_payout_structure(
            {
                str(item.place): item.amount
                for item in body.payout_structure
            }
        ),
        is_excluded=body.is_excluded,
    )

    updated_summary = await get_finance_summary(
        ctx,
    )
    updated = next(
        (
            entry
            for entry in updated_summary.seasons
            if entry.league_id == body.league_id
            and entry.season == body.season
        ),
        None,
    )

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Saved finance entry could not be reloaded",
        )

    return updated


async def reset_finance_entry(
    body: FinanceSeasonReset,
    ctx: Context,
) -> FinanceLeagueSeasonEntry:
    _require_finance_context(
        ctx,
    )

    league_ids = [
        body.league_id,
    ]
    finance_entries_by_key = await get_finance_entries_by_key(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
        league_ids=league_ids,
    )
    finance_entry = finance_entries_by_key.get(
        (
            body.league_id,
            body.season,
        )
    )

    if finance_entry is not None:
        await delete_finance_entry(
            db=ctx.db,
            finance_entry=finance_entry,
        )

    updated_summary = await get_finance_summary(
        ctx,
    )
    updated = next(
        (
            entry
            for entry in updated_summary.seasons
            if entry.league_id == body.league_id
            and entry.season == body.season
        ),
        None,
    )

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League season not available in finance tracker",
        )

    return updated


async def save_finance_defaults(
    body: FinanceDefaultsUpdate,
    ctx: Context,
) -> FinanceSummaryResponse:
    _require_finance_context(
        ctx,
    )

    await upsert_finance_user_defaults(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
        buy_in_amount=_normalize_default_buy_in(
            body.buy_in_amount,
        ),
        payout_structure=_normalize_default_payouts(
            body.payout_structure,
        ),
    )

    return await get_finance_summary(
        ctx,
    )


async def get_finance_timeline(
    ctx: Context,
    season: str | None = None,
) -> FinanceTimelineResponse:
    _require_finance_context(ctx)

    raw_owned_rows = await get_owned_roster_rows(
        db=ctx.db,
        connection=ctx.connection,
    )
    hidden_league_ids = await get_hidden_league_ids(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
    )
    owned_rows = [
        (roster, league)
        for roster, league in raw_owned_rows
        if league.league_id not in hidden_league_ids
    ]

    if season is not None:
        owned_rows = [
            (roster, league)
            for roster, league in owned_rows
            if league.season == season
        ]

    if not owned_rows:
        return FinanceTimelineResponse(points=[])

    league_ids = [league.league_id for _, league in owned_rows]

    current_week = 0
    if ctx.sleeper is not None and hasattr(ctx.sleeper, "read"):
        try:
            state = await ctx.sleeper.read.get_nfl_state()
            current_week = int(getattr(state, "week", 0) or 0)
        except Exception:
            current_week = 0

    if current_week < 1:
        current_week = 1

    cache_key = _build_finance_timeline_cache_key(
        ctx=ctx,
        league_ids=league_ids,
        season=season,
        current_week=current_week,
    )
    if ctx.redis is not None:
        try:
            cached = await ctx.redis.get(cache_key)
            if cached:
                payload = json.loads(cached)
                points = payload.get("points") or []
                return FinanceTimelineResponse(
                    points=[
                        {
                            "week": int(p.get("week")),
                            "label": p.get("label") or f"Week {p.get('week')}",
                            "actual_amount": float(p.get("actual_amount") or 0),
                            "projected_amount": float(p.get("projected_amount") or 0),
                        }
                        for p in points
                    ],
                )
        except Exception:
            pass

    summary = await get_finance_summary(ctx)
    entries = summary.seasons
    if season is not None:
        entries = [e for e in entries if e.season == season]
    entries = [e for e in entries if not getattr(e, "is_excluded", False)]

    # Resolve projection settings
    finance_projection_settings = (
        ctx.site_user.settings.get("finance_projection_settings")
        if ctx.site_user and ctx.site_user.settings
        else None
    )
    draft_pick_projection_settings = (
        ctx.site_user.settings.get("draft_pick_projection_settings")
        if ctx.site_user and ctx.site_user.settings
        else None
    )
    effective_projection_settings = resolve_finance_projection_settings(
        finance_settings=finance_projection_settings,
        draft_pick_projection_settings=draft_pick_projection_settings,
        authenticated=ctx.site_user is not None,
    )

    # Sync missing weekly metrics for active in-season leagues
    leagues_by_id = {league.league_id: league for _, league in owned_rows}
    roster_by_league_id = {league.league_id: roster for roster, league in owned_rows}

    active_leagues = [
        league
        for _, league in owned_rows
        if league.status in ("in_season", "post_season")
    ]
    if active_leagues and ctx.sleeper is not None:
        try:
            await sync_league_weekly_matchups(
                db=ctx.db,
                sleeper=ctx.sleeper,
                leagues=active_leagues,
                current_week=current_week,
                redis=ctx.redis,
            )
        except Exception as exc:
            logger.warning("Failed to sync weekly matchups for finance timeline: %s", exc)

    all_metrics = await get_league_weekly_metrics(
        db=ctx.db,
        league_ids=league_ids,
        max_week=current_week,
    )

    metrics_by_league: dict[str, list[Any]] = {}
    for m in all_metrics:
        metrics_by_league.setdefault(m.league_id, []).append(m)

    is_completed_season = bool(owned_rows) and all(
        league.status == "complete" for _, league in owned_rows
    )
    total_actual_w = round(
        sum(float(e.winnings_amount or 0) for e in entries),
        2,
    )

    max_week = max(current_week, 1)
    weeks = list(range(1, max_week + 1))
    points = []

    for w in weeks:
        active_method = resolve_draft_pick_projection_method(
            current_week=w,
            settings=effective_projection_settings,
        )

        total_projected_w = 0.0

        for entry in entries:
            league_id = entry.league_id
            league_obj = leagues_by_id.get(league_id)
            user_roster = roster_by_league_id.get(league_id)
            user_roster_id = user_roster.roster_id if user_roster else None
            league_metrics = metrics_by_league.get(league_id, [])

            if not league_metrics or user_roster_id is None:
                total_projected_w += float(entry.projected_winnings_amount or 0)
                continue

            roster_stats: dict[int, dict[str, float]] = {}
            for m in league_metrics:
                if m.week > w:
                    continue
                r_stats = roster_stats.setdefault(
                    m.roster_id,
                    {
                        "cum_points": 0.0,
                        "cum_max_points": 0.0,
                        "cum_wins": 0.0,
                        "starter_war": 0.0,
                        "roster_war": 0.0,
                        "sleeper_proj": 0.0,
                        "ktc_val": 0.0,
                        "fc_val": 0.0,
                    },
                )
                r_stats["cum_points"] += m.points
                r_stats["cum_max_points"] += m.max_points
                r_stats["cum_wins"] += m.wins
                if m.week == w:
                    r_stats["starter_war"] = m.starter_war or 0.0
                    r_stats["roster_war"] = m.roster_war or 0.0
                    r_stats["sleeper_proj"] = m.sleeper_projection or 0.0
                    r_stats["ktc_val"] = m.ktc_redraft or 0.0
                    r_stats["fc_val"] = m.fantasycalc_redraft or 0.0

            if user_roster_id not in roster_stats:
                total_projected_w += float(entry.projected_winnings_amount or 0)
                continue

            def _rank_key(item: tuple[int, dict[str, float]]):
                r_id, stats = item
                if active_method == "points_for":
                    return (stats["cum_points"], stats["cum_max_points"], -r_id)
                if active_method == "max_pf":
                    return (stats["cum_max_points"], stats["cum_points"], -r_id)
                if active_method == "redraft_starter_war":
                    return (stats["starter_war"], stats["cum_points"], -r_id)
                if active_method == "redraft_roster_war":
                    return (stats["roster_war"], stats["cum_points"], -r_id)
                if active_method == "sleeper_projection":
                    return (stats["sleeper_proj"], stats["cum_points"], -r_id)
                if active_method == "ktc_redraft":
                    return (stats["ktc_val"], stats["cum_points"], -r_id)
                if active_method == "fantasycalc_redraft":
                    return (stats["fc_val"], stats["cum_points"], -r_id)
                return (stats["cum_wins"], stats["cum_points"], -r_id)

            sorted_rosters = sorted(roster_stats.items(), key=_rank_key, reverse=True)
            roster_rank = next(
                (idx + 1 for idx, (r_id, _) in enumerate(sorted_rosters) if r_id == user_roster_id),
                None,
            )

            if roster_rank is None:
                total_projected_w += float(entry.projected_winnings_amount or 0)
                continue

            payout_dict = {
                str(p.place): p.amount
                for p in (entry.payout_structure or [])
            }
            playoff_teams = league_obj.playoff_teams if league_obj else 6
            expected = calculate_expected_winnings_from_seed(
                payout_structure=payout_dict,
                projected_seed=roster_rank,
                total_rosters=entry.total_rosters,
                playoff_teams=playoff_teams,
            )
            if expected is not None:
                total_projected_w += expected
            else:
                total_projected_w += float(entry.projected_winnings_amount or 0)

        points.append(
            {
                "week": w,
                "label": f"Week {w}",
                "actual_amount": total_actual_w if is_completed_season else 0.0,
                "projected_amount": round(total_projected_w, 2),
            }
        )

    result = FinanceTimelineResponse(
        points=[
            {
                "week": p["week"],
                "label": p["label"],
                "actual_amount": p["actual_amount"],
                "projected_amount": p["projected_amount"],
            }
            for p in points
        ]
    )
    if ctx.redis is not None:
        try:
            await ctx.redis.set(
                cache_key,
                json.dumps({"points": points}),
                ex=FINANCE_TIMELINE_CACHE_TTL_SECONDS,
            )
        except Exception:
            pass
    return result



async def save_finance_league_defaults(
    body: FinanceLeagueDefaultsUpdate,
    ctx: Context,
) -> FinanceSummaryResponse:
    _require_finance_context(
        ctx,
    )

    if not body.league_family_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one league family is required",
        )

    summary = await get_finance_summary(
        ctx,
    )
    valid_family_ids = {
        entry.league_family_id
        for entry in summary.seasons
    }

    for league_family_id in body.league_family_ids:
        if league_family_id not in valid_family_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"League family {league_family_id} is not available "
                    "in the finance tracker"
                ),
            )

        await upsert_finance_league_default(
            db=ctx.db,
            site_user_id=ctx.site_user.id,
            league_family_id=league_family_id,
            buy_in_amount=_normalize_default_buy_in(
                body.buy_in_amount,
            ),
            payout_structure=_normalize_default_payouts(
                body.payout_structure,
            ),
        )

    return await get_finance_summary(
        ctx,
    )
