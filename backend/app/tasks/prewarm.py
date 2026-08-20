"""
WAR cache pre-warm task.

Fired by sync_user_data_task after a successful user sync.  Runs entirely in
the worker process and writes results to the Redis fingerprint cache so that the
API process can skip CPU-bound WAR calculations on the next dashboard or league-
details cold load.
"""

import logging

from app.analytics.war.redraft.singleton import war_service
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.crud.sleeper.user import get_userid_by_username
from app.integrations.sleeper.factory import get_sleeper_client
from app.infrastructure.redis.client import RedisClient
from app.services.leagues.selection import (
    get_visible_owned_league_rows_by_sleeper_user_id,
)
from app.services.dashboard.service import (
    CURRENT_DASHBOARD_STATUSES,
    get_league_season,
    load_shared_war_data_by_season,
)

logger = logging.getLogger(__name__)


async def prewarm_war_cache_for_user(username: str) -> None:
    """
    Loads the user's active leagues and pre-warms the Redis WAR fingerprint
    cache for each one.

    The fingerprint cache is keyed on (season, total_rosters, scoring_settings,
    roster_positions) so leagues that share settings (e.g. two 12-team leagues
    with identical scoring) only require one thread-pool computation.  All
    subsequent leagues hit the fingerprint cache at the Redis level.

    This does NOT compete with the API process for CPU \u2014 it runs in the worker
    process and only writes to Redis.  The API's calculate_war_by_league call
    will read from that Redis cache via calculate_with_shared_cache and skip the
    thread-pool work entirely.
    """

    try:
        from redis.asyncio import Redis

        redis_conn = Redis.from_url(settings.REDIS_URL)
        redis = RedisClient(redis=redis_conn)

        async with AsyncSessionLocal() as db:
            sleeper = await get_sleeper_client()

            user_id = await get_userid_by_username(db, sleeper, username)
            if user_id is None:
                logger.warning(
                    "WAR pre-warm: no Sleeper user found for username=%s",
                    username,
                )
                return

            visible_rows = await get_visible_owned_league_rows_by_sleeper_user_id(
                db=db,
                sleeper_user_id=user_id,
                site_user_id=None,
            )

            current_rows = [
                row
                for row in visible_rows
                if row.league.status in CURRENT_DASHBOARD_STATUSES
            ]
            selected_rows = current_rows if current_rows else visible_rows

            leagues = {
                row.league.league_id: {
                    "league": row.league,
                    "user_rosters": [row.roster],
                }
                for row in selected_rows
            }

            if not leagues:
                logger.info(
                    "WAR pre-warm: no active leagues for username=%s",
                    username,
                )
                return

            shared_by_season = await load_shared_war_data_by_season(
                db=db,
                leagues=leagues,
            )

        # DB session closed; compute WAR outside the session scope.
        # calculate_with_shared_cache only needs league ORM attrs (season,
        # total_rosters, scoring_settings, roster_positions) which are already
        # loaded.  No further DB access occurs here.
        league_count = len(leagues)
        logger.info(
            "WAR pre-warm: computing for username=%s leagues=%d",
            username,
            league_count,
        )

        import asyncio

        tasks = [
            war_service.calculate_with_shared_cache(
                redis=redis,
                league=data["league"],
                shared=shared_by_season[get_league_season(data["league"])],
            )
            for data in leagues.values()
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(
            "WAR pre-warm: completed username=%s leagues=%d",
            username,
            league_count,
        )

    except Exception:
        logger.warning(
            "WAR pre-warm: failed for username=%s",
            username,
            exc_info=True,
        )
    finally:
        try:
            await redis_conn.aclose()
        except Exception:
            pass
