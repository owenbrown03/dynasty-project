from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import Iterable

from app.core.concurrency import heavy_work_semaphore
from app.analytics.war.redraft.singleton import (
    war_service,
)
from app.crud.value import (
    get_player_values,
)
from app.services.waivers.dynasty import (
    DYNASTY_FANTASY_POSITIONS,
)
from app.services.personal_values import (
    hydrate_personal_player_values,
)
from app.services.war.shared import (
    build_cached_dynasty_projections_by_player_id,
)
from app.services.finance import (
    build_dashboard_finance_metrics_by_league_id,
)
from app.services.leagues.details import (
    LeagueDetails,
    build_cached_league_roster_construction_targets,
)

from .cards import (
    build_league_cards,
)
from .crud import (
    get_all_league_rosters,
)
from app.crud.sleeper.personal import get_focused_league_ids
from app.services.leagues.selection import (
    get_visible_owned_league_rows_by_sleeper_user_id,
)
from app.crud.sleeper.personal import get_league_sort_orders
from app.crud.sleeper.user import get_userid_by_username
from app.core.database import AsyncSessionLocal


logger = logging.getLogger(__name__)

CURRENT_DASHBOARD_STATUSES = {
    "pre_draft",
    "drafting",
    "in_season",
    "post_season",
}
DASHBOARD_CACHE_VERSION = "v1"
DASHBOARD_CACHE_TTL_SECONDS = 10 * 60


def build_dashboard_cache_key(
    *,
    user_id: str,
    site_user_id,
    league_ids: Iterable[str],
    sort_order: dict[str, int],
    cheap: bool = False,
) -> str:
    return (
        f"dashboard:{DASHBOARD_CACHE_VERSION}:"
        + json.dumps(
            {
                "user_id": user_id,
                "site_user_id": (
                    str(site_user_id)
                    if site_user_id is not None
                    else None
                ),
                "league_ids": sorted(league_ids),
                "sort_order": sorted(
                    sort_order.items(),
                ),
                "cheap": cheap,
            },
            sort_keys=True,
        )
    )


def build_dashboard_cache_prefix() -> str:
    return f"dashboard:{DASHBOARD_CACHE_VERSION}:"


async def _prefetch_trade_signals(username: str, site_user_id):
    try:
        async with AsyncSessionLocal() as db:
            from app.crud.sleeper.trade import get_trade_signals
            from app.integrations.sleeper.factory import get_sleeper_client
            from app.infrastructure.redis.client import RedisClient
            from app.core.config import settings
            from redis.asyncio import Redis

            sleeper = await get_sleeper_client()
            redis = RedisClient(redis=Redis.from_url(settings.REDIS_URL))

            await get_trade_signals(
                db,
                sleeper,
                username,
                site_user_id=site_user_id,
                redis=redis,
            )
            logger.info("Trade signals prefetch completed for %s", username)
    except Exception:
        logger.warning("Trade signals prefetch failed for %s", username, exc_info=True)


def get_league_season(
    league,
) -> int:
    """
    Converts the DB league season into the integer used by WAR projections.

    Keeping this isolated makes errors easier to diagnose if old leagues
    or malformed season data ever enter the dashboard query.
    """

    try:
        return int(league.season)
    except (
        TypeError,
        ValueError,
    ) as error:
        raise ValueError(
            f"League {league.league_id} has invalid season "
            f"{league.season!r}"
        ) from error


def build_league_rostered_player_ids(
    rosters,
    league_war_by_player_id,
) -> set[str]:
    """
    Returns all rostered players who exist in the league's WAR universe.

    We intentionally do not restrict this function to QB/RB/WR/TE because
    KTC, FantasyCalc, roster counts, and player counts should still include
    any rostered player that has a value record.

    Dynasty projection filtering happens separately.
    """

    return {
        player_id
        for roster in rosters
        for player_id in (roster.players or [])
        if player_id in league_war_by_player_id
    }


async def build_dynasty_war_by_player_id(
    *,
    redis,
    league_war_by_player_id,
    rostered_player_ids: Iterable[str],
):
    """
    Builds dynasty WAR only for players currently rostered in this league.

    Dynasty WAR is league-context-specific because the input redraft WAR
    already reflects that league's scoring, lineup requirements, and
    replacement levels.
    """

    return await build_cached_dynasty_projections_by_player_id(
        redis=redis,
        player_wars=[
            league_war_by_player_id[player_id]
            for player_id in rostered_player_ids
            if (
                player_id in league_war_by_player_id
                and league_war_by_player_id[
                    player_id
                ].position
                in DYNASTY_FANTASY_POSITIONS
            )
        ],
    )


async def load_shared_war_data_by_season(
    *,
    db,
    leagues,
) -> dict[int, object]:
    """
    WAR shared data is season-specific.

    Most dashboard users will only have one season, but grouping by season
    prevents an old league from accidentally using current-season shared
    projections or replacement data.
    """

    seasons = sorted(
        {
            get_league_season(
                league_data["league"],
            )
            for league_data in leagues.values()
        }
    )

    shared_results = await asyncio.gather(
        *[
            war_service.load_shared_data(
                db,
                season,
            )
            for season in seasons
        ]
    )

    return dict(
        zip(
            seasons,
            shared_results,
        )
    )


async def calculate_war_by_league(
    *,
    redis,
    leagues,
    shared_by_season,
) -> dict[str, list]:
    """
    Calculates redraft WAR independently for every league.

    When a Redis client is provided the fingerprint cache is consulted first
    so that a pre-warmed result (written by the post-sync worker task) is
    returned without any thread-pool CPU work.

    Do not flatten these results into one global player map afterward.
    The same player can have different WAR values across leagues.
    """

    league_ids = list(
        leagues.keys(),
    )

    sem = asyncio.Semaphore(4)

    async def _task(league_id: str):
        async with sem:
            league = leagues[league_id]["league"]
            return await war_service.calculate_with_shared_cache(
                redis=redis,
                league=league,
                shared=shared_by_season[
                    get_league_season(league)
                ],
            )

    tasks = [
        _task(league_id)
        for league_id in league_ids
    ]

    results_per_league = await asyncio.gather(
        *tasks,
        return_exceptions=False,
    )

    return dict(
        zip(
            league_ids,
            results_per_league,
        )
    )


async def _build_single_league_player_map(
    *,
    db,
    redis,
    site_user_id,
    league_id,
    league,
    league_war_players,
    league_rosters,
):
    """Build player map for a single league (extracted for parallelization)."""

    league_war_by_player_id = {
        player.player_id: player
        for player in league_war_players
    }

    rostered_player_ids = build_league_rostered_player_ids(
        rosters=league_rosters,
        league_war_by_player_id=league_war_by_player_id,
    )

    dynasty_war_by_player_id = await build_dynasty_war_by_player_id(
        redis=redis,
        league_war_by_player_id=league_war_by_player_id,
        rostered_player_ids=rostered_player_ids,
    )

    league_player_values = await get_player_values(
        db=db,
        player_ids=rostered_player_ids,
        redraft_war_players=league_war_players,
        dynasty_war_by_player_id=dynasty_war_by_player_id,
    )
    league_player_values = await hydrate_personal_player_values(
        db=db,
        site_user_id=site_user_id,
        league=league,
        player_values=league_player_values,
        redis=redis,
    )

    player_map = {
        player.player_id: player
        for player in league_player_values
    }

    logger.info(
        "Dashboard values league=%s rostered=%s dynasty_projected=%s enriched=%s",
        league_id,
        len(rostered_player_ids),
        len(dynasty_war_by_player_id),
        len(league_player_values),
    )

    return league_id, player_map


async def build_player_maps_by_league(
    *,
    db,
    redis,
    site_user_id,
    leagues,
    all_rosters,
    war_results_by_league_id,
) -> dict[str, dict]:
    """
    Builds:

        {
            league_id: {
                player_id: PlayerValue,
            },
        }

    Every PlayerValue in a league map contains:
    - market values
    - redraft WAR for that exact league
    - dynasty WAR projected from that exact league's redraft WAR
    """

    sem = asyncio.Semaphore(4)

    async def _task(league_id):
        async with sem:
            async with AsyncSessionLocal() as task_db:
                return await _build_single_league_player_map(
                    db=task_db,
                    redis=redis,
                    site_user_id=site_user_id,
                    league_id=league_id,
                    league=leagues[league_id]["league"],
                    league_war_players=war_results_by_league_id[league_id],
                    league_rosters=all_rosters.get(league_id, []),
                )

    tasks = [_task(league_id) for league_id in leagues]
    results = await asyncio.gather(*tasks)

    return {league_id: player_map for league_id, player_map in results}


def _apply_focus_flags(
    response: dict,
    focused_league_ids: set[str],
) -> dict:
    """Overlays starred-league flags post-cache so focus changes show
    immediately without invalidating the dashboard cache."""
    for card in response.get("leagues", []):
        card["is_focused"] = (
            card.get("league_id") in focused_league_ids
        )

    return response



async def get_user_dashboard(
    db,
    redis,
    sleeper,
    username: str,
    *,
    site_user_id=None,
    cheap: bool = False,
):
    """
    Returns the user's cross-league dashboard.

    Redis is used for cross-league dynasty projection caching after the
    league-specific redraft WAR inputs are computed.
    """

    t_total = time.monotonic()

    user_id = await get_userid_by_username(
        db,
        sleeper,
        username,
    )

    sort_order = await get_league_sort_orders(
        db=db,
        user_id=user_id,
    )

    visible_rows = await get_visible_owned_league_rows_by_sleeper_user_id(
        db=db,
        sleeper_user_id=user_id,
        site_user_id=site_user_id,
    )
    current_rows = [
        row
        for row in visible_rows
        if row.league.status in CURRENT_DASHBOARD_STATUSES
    ]

    selected_rows = (
        current_rows
        if current_rows
        else visible_rows
    )

    leagues = {
        row.league.league_id: {
            "league": row.league,
            "user_rosters": [row.roster],
        }
        for row in selected_rows
    }

    if not leagues:
        return {
            "leagues": [],
        }

    league_ids = list(
        leagues.keys(),
    )

    focused_league_ids: set[str] = set()
    if site_user_id is not None:
        focused_league_ids = await get_focused_league_ids(
            db=db,
            site_user_id=site_user_id,
        )

    dashboard_cache_key = build_dashboard_cache_key(
        user_id=user_id,
        site_user_id=site_user_id,
        league_ids=league_ids,
        sort_order=sort_order,
        cheap=cheap,
    )

    if redis is not None:
        cached_payload = await redis.get(
            dashboard_cache_key,
        )
        if cached_payload:
            logger.info(
                "Dashboard source=redis user=%s leagues=%s elapsed=%.1fs",
                username,
                len(league_ids),
                time.monotonic() - t_total,
            )
            return _apply_focus_flags(
                json.loads(cached_payload),
                focused_league_ids,
            )

    if cheap:
        all_rosters = await get_all_league_rosters(
            db,
            league_ids,
        )
        league_cards = build_league_cards(
            leagues=leagues,
            all_rosters=all_rosters,
            player_maps_by_league_id={},
            roster_construction_targets_by_league_id={},
            finance_metrics_by_league_id={},
            user_id=user_id,
        )
        expensive_fields = [
            "ktc_value", "ktc_rank",
            "fc_value", "fc_rank",
            "dynasty_starter_war", "dynasty_starter_war_rank",
            "dynasty_roster_war", "dynasty_roster_war_rank",
            "redraft_starter_war", "redraft_starter_war_rank",
            "redraft_roster_war", "redraft_roster_war_rank",
            "my_dynasty_starter_war", "my_dynasty_starter_war_rank",
            "my_dynasty_roster_war", "my_dynasty_roster_war_rank",
            "my_redraft_starter_war", "my_redraft_starter_war_rank",
            "my_redraft_roster_war", "my_redraft_roster_war_rank",
            "average_age", "age_rank",
            "projected_payout", "projected_seed", "buy_in_amount",
            "roster_construction_alignment_pct", "roster_construction_moves_needed"
        ]
        for card in league_cards:
            for field in expensive_fields:
                card[field] = None
            card["is_cheap_data"] = True

        league_cards.sort(
            key=lambda league: (
                sort_order.get(league["league_id"], 9999),
                league["league_name"].lower(),
            ),
        )

        response = _apply_focus_flags(
            {
                "leagues": league_cards,
                "is_cheap_data": True,
            },
            focused_league_ids,
        )

        if redis is not None:
            await redis.set(
                dashboard_cache_key,
                json.dumps(response),
                ttl_seconds=DASHBOARD_CACHE_TTL_SECONDS,
            )

        logger.info(
            "Dashboard cheap cold total=%.2fs user=%s leagues=%d",
            time.monotonic() - t_total,
            username,
            len(leagues),
        )
        return response

    async with heavy_work_semaphore:
        t_rosters = time.monotonic()
        all_rosters = await get_all_league_rosters(
            db,
            league_ids,
        )
        logger.info("Dashboard get_rosters took %.2fs", time.monotonic() - t_rosters)

        t_shared = time.monotonic()
        shared_by_season = (
            await load_shared_war_data_by_season(
                db=db,
                leagues=leagues,
            )
        )
        logger.info("Dashboard load_shared took %.2fs", time.monotonic() - t_shared)

        t_war = time.monotonic()
        war_results_by_league_id = (
            await calculate_war_by_league(
                redis=redis,
                leagues=leagues,
                shared_by_season=shared_by_season,
            )
        )
        logger.info("Dashboard calculate_war took %.2fs (%d leagues)", time.monotonic() - t_war, len(leagues))

        t_parallel = time.monotonic()

        player_maps_by_league_id_coro = build_player_maps_by_league(
            db=db,
            redis=redis,
            site_user_id=site_user_id,
            leagues=leagues,
            all_rosters=all_rosters,
            war_results_by_league_id=war_results_by_league_id,
        )

        roster_construction_service = LeagueDetails()

        async def _build_roster_construction():
            sem = asyncio.Semaphore(4)

            async def _rc_task(league_id):
                async with sem:
                    async with AsyncSessionLocal() as task_db:
                        league = leagues[league_id]["league"]
                        league_rosters = all_rosters.get(league_id, [])
                        current_shared = shared_by_season[get_league_season(league)]
                        seasonal_results = await roster_construction_service.build_roster_construction_seasonal_results(
                            db=task_db,
                            redis=redis,
                            league=league,
                            players=current_shared.players,
                            current_shared=current_shared,
                        )
                        return league_id, await build_cached_league_roster_construction_targets(
                            redis=redis,
                            league=league,
                            roster_rows=league_rosters,
                            seasonal_results=seasonal_results,
                        )
            results = await asyncio.gather(*[_rc_task(lid) for lid in leagues])
            return dict(results)

        finance_coro = build_dashboard_finance_metrics_by_league_id(
            db=db,
            redis=redis,
            site_user_id=site_user_id,
            owned_rows=[
                (row.roster, row.league)
                for row in selected_rows
            ],
        )

        player_maps_by_league_id, roster_construction_targets_by_league_id, finance_metrics_by_league_id = (
            await asyncio.gather(
                player_maps_by_league_id_coro,
                _build_roster_construction(),
                finance_coro,
            )
        )
        logger.info("Dashboard parallel phase took %.2fs", time.monotonic() - t_parallel)

    t_cards = time.monotonic()
    league_cards = build_league_cards(
        leagues=leagues,
        all_rosters=all_rosters,
        player_maps_by_league_id=(
            player_maps_by_league_id
        ),
        roster_construction_targets_by_league_id=(
            roster_construction_targets_by_league_id
        ),
        finance_metrics_by_league_id=(
            finance_metrics_by_league_id
        ),
        user_id=user_id,
    )
    league_cards.sort(
        key=lambda league: (
            sort_order.get(league["league_id"], 9999),
            league["league_name"].lower(),
        ),
    )
    logger.info("Dashboard build_cards took %.2fs", time.monotonic() - t_cards)

    response = _apply_focus_flags(
        {
            "leagues": league_cards,
        },
        focused_league_ids,
    )

    if redis is not None:
        await redis.set(
            dashboard_cache_key,
            json.dumps(response),
            ttl_seconds=DASHBOARD_CACHE_TTL_SECONDS,
        )

    logger.info(
        "Dashboard cold total=%.1fs user=%s leagues=%d",
        time.monotonic() - t_total,
        username,
        len(leagues),
    )

    return response
