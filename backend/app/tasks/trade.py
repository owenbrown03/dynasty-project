import logging
import uuid

from app.core.broker import broker
from app.core.database import AsyncSessionLocal
from app.crud.sleeper.leaguemate import sync_leaguemates
from app.infrastructure.redis.manager import RedisManager
from app.integrations.sleeper.singleton import get_worker_sleeper_client

logger = logging.getLogger(__name__)

LEAGUEMATE_SYNC_LOCK_TTL_SECONDS = 20 * 60


def _leaguemate_sync_lock_key(
    username: str,
) -> str:
    return f"sync:leaguemates:{username}"


async def _acquire_leaguemate_sync_lock(
    username: str,
) -> str | None:
    redis = await RedisManager.get()
    token = str(
        uuid.uuid4(),
    )

    acquired = await redis.set(
        _leaguemate_sync_lock_key(
            username,
        ),
        token,
        ex=LEAGUEMATE_SYNC_LOCK_TTL_SECONDS,
        nx=True,
    )

    if acquired:
        return token

    return None


async def _release_leaguemate_sync_lock(
    username: str,
    token: str,
) -> None:
    redis = await RedisManager.get()
    key = _leaguemate_sync_lock_key(
        username,
    )
    current = await redis.get(
        key,
    )

    if current == token:
        await redis.delete(
            key,
        )


@broker.task
async def sync_leaguemates_task(username: str):
    lock_token = await _acquire_leaguemate_sync_lock(
        username,
    )

    if lock_token is None:
        logger.info(
            "Skipping leaguemate sync for %s because one is already running",
            username,
        )
        return {
            "status": "skipped",
            "reason": "already_running",
            "username": username,
        }

    async with AsyncSessionLocal() as db:
        try:
            sleeper = await get_worker_sleeper_client()

            result = await sync_leaguemates(
                db,
                sleeper,
                username,
            )

            await db.commit()
            return result
        finally:
            await _release_leaguemate_sync_lock(
                username,
                lock_token,
            )
