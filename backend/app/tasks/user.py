import asyncio

from app.core.broker import broker
from app.core.database import AsyncSessionLocal
from app.crud.sleeper.user import sync_user_data
from app.integrations.sleeper.singleton import get_worker_sleeper_client
from app.infrastructure.redis.client import RedisClient
from app.core.config import settings
from app.services.dashboard.service import build_dashboard_cache_prefix
from app.services.leagues.details import build_league_details_cache_prefix
from app.tasks.prewarm import prewarm_war_cache_for_user


@broker.task
async def sync_user_data_task(username: str):
    from redis.asyncio import Redis

    redis_conn = Redis.from_url(settings.REDIS_URL)
    redis = RedisClient(
        redis=redis_conn,
    )

    async with AsyncSessionLocal() as db:
        sleeper = await get_worker_sleeper_client()

        result = await sync_user_data(
            db,
            sleeper,
            username,
        )

        await db.commit()

    try:
        await redis.delete_prefix(
            build_dashboard_cache_prefix(),
        )
        await redis.delete_prefix(
            build_league_details_cache_prefix(),
        )

        # Pre-warm the Redis WAR fingerprint cache so the next dashboard cold load
        # skips the CPU-bound WAR computation.  Fire-and-forget; errors are logged
        # inside prewarm_war_cache_for_user and never surface to the caller.
        asyncio.create_task(prewarm_war_cache_for_user(username))

        return result
    finally:
        await redis_conn.aclose()


@broker.task
async def sync_active_users_current_season_task():
    """
    Periodic background job that performs a fast current-season sync for all active users.
    """
    from redis.asyncio import Redis
    from app.crud.sleeper.user import (
        get_active_sleeper_usernames,
        sync_user_current_season_data,
    )

    redis_conn = Redis.from_url(settings.REDIS_URL)
    redis = RedisClient(redis=redis_conn)

    try:
        async with AsyncSessionLocal() as db:
            active_usernames = await get_active_sleeper_usernames(db)
            if not active_usernames:
                return {"status": "skipped", "reason": "no_active_users"}

            sleeper = await get_worker_sleeper_client()
            results = []

            for username in active_usernames:
                try:
                    res = await sync_user_current_season_data(
                        db,
                        sleeper,
                        username,
                    )
                    results.append(res)
                    await db.commit()
                except Exception as exc:
                    results.append({"status": "error", "username": username, "error": str(exc)})

        await redis.delete_prefix(build_dashboard_cache_prefix())
        await redis.delete_prefix(build_league_details_cache_prefix())

        # Prewarm WAR for active users
        for username in active_usernames:
            asyncio.create_task(prewarm_war_cache_for_user(username))

        return {
            "status": "completed",
            "active_users_count": len(active_usernames),
            "results": results,
        }
    finally:
        await redis_conn.aclose()

