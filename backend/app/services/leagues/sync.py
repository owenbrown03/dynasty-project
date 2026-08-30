import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.sleeper.league import sync_leagues
from app.infrastructure.redis.client import RedisClient
from app.integrations.sleeper.client import SleeperClient
from app.services.dashboard.service import build_dashboard_cache_prefix
from app.services.leagues.details import build_league_details_cache_prefix

logger = logging.getLogger(__name__)


async def sync_single_league(
    db: AsyncSession,
    sleeper: SleeperClient,
    redis: RedisClient,
    league_id: str,
) -> dict:
    """
    Directly fetches fresh league data, rosters, users, and transactions for a single league
    from Sleeper, persists them to Postgres, and invalidates Redis caches.
    """
    logger.info("Starting single league sync for league_id=%s", league_id)

    raw_league = await sleeper.read.get_league(league_id)
    if not raw_league:
        return {
            "status": "not_found",
            "league_id": league_id,
        }

    state = await sleeper.read.get_nfl_state()
    curr_week = (
        state.effective_week
        if hasattr(state, "effective_week")
        else max(int(state.week), 1)
    )

    sync_result = await sync_leagues(
        db=db,
        raw_leagues=[raw_league],
        curr_week=curr_week,
        sleeper=sleeper,
        force=True,
        existing_refresh="full",
        is_current_season=True,
    )

    await db.commit()

    # Invalidate cached league details and dashboard views
    await redis.delete_prefix(build_league_details_cache_prefix())
    await redis.delete_prefix(build_dashboard_cache_prefix())

    logger.info(
        "Single league sync completed for league_id=%s: %s",
        league_id,
        sync_result,
    )

    return {
        "status": "completed",
        "league_id": league_id,
        "result": sync_result,
    }
