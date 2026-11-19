from datetime import datetime
import logging
import uuid
from zoneinfo import ZoneInfo

from app.core.broker import broker
from app.core.config import settings
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
async def sync_leaguemates_task(username: str, force: bool = False):
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
                force=force,
            )

            await db.commit()
            return result
        finally:
            await _release_leaguemate_sync_lock(
                username,
                lock_token,
            )


def is_in_leaguemate_sync_window(
    now: datetime | None = None,
    tz_name: str | None = None,
    start_hour: int | None = None,
    end_hour: int | None = None,
) -> tuple[bool, datetime]:
    """
    Checks if the given time (or current time) is within the scheduled overnight window.
    Defaults to 3:00 AM - 5:00 AM America/Denver (Mountain Time).
    """
    tz_str = tz_name or getattr(settings, "LEAGUEMATE_SYNC_TIMEZONE", "America/Denver")
    tz = ZoneInfo(tz_str)
    if now is None:
        local_now = datetime.now(tz)
    elif now.tzinfo is None:
        local_now = now.replace(tzinfo=tz)
    else:
        local_now = now.astimezone(tz)

    start = (
        start_hour
        if start_hour is not None
        else getattr(settings, "LEAGUEMATE_SYNC_START_HOUR", 3)
    )
    end = (
        end_hour
        if end_hour is not None
        else getattr(settings, "LEAGUEMATE_SYNC_END_HOUR", 5)
    )

    in_window = start <= local_now.hour < end
    return in_window, local_now


@broker.task
async def run_daily_leaguemate_syncs_task(
    force: bool = False,
    now: datetime | None = None,
):
    """
    Daily scheduled job that iterates through active users with linked site accounts
    and enqueues deep leaguemate synchronizations during the scheduled overnight window.
    """
    from app.crud.sleeper.user import get_active_sleeper_usernames

    in_window, local_now = is_in_leaguemate_sync_window(now=now)

    if not force and not in_window:
        logger.info(
            "Skipping daily leaguemate syncs because current local time %s is outside overnight window (%02d:00-%02d:00 %s)",
            local_now.strftime("%Y-%m-%d %H:%M:%S %Z"),
            settings.LEAGUEMATE_SYNC_START_HOUR,
            settings.LEAGUEMATE_SYNC_END_HOUR,
            settings.LEAGUEMATE_SYNC_TIMEZONE,
        )
        return {
            "status": "skipped",
            "reason": "outside_scheduled_window",
            "local_time": local_now.isoformat(),
        }

    today_str = local_now.strftime("%Y-%m-%d")
    redis = await RedisManager.get()
    daily_run_key = f"leaguemates:daily_sync:last_run:{today_str}"
    already_ran = await redis.get(daily_run_key)

    if not force and already_ran:
        logger.info(
            "Skipping daily leaguemate syncs because it already ran today (%s)",
            today_str,
        )
        return {
            "status": "skipped",
            "reason": "already_ran_today",
            "date": today_str,
        }

    async with AsyncSessionLocal() as db:
        active_usernames = await get_active_sleeper_usernames(
            db,
            accounts_only=True,
        )

    if not active_usernames:
        return {"status": "skipped", "reason": "no_account_linked_users"}

    logger.info(
        "Enqueuing daily overnight leaguemate syncs for %d account-linked users: %s",
        len(active_usernames),
        active_usernames,
    )

    for username in active_usernames:
        await sync_leaguemates_task.kiq(username, force=True)

    # Record 48h TTL for today's run and legacy 24h key
    await redis.set(daily_run_key, "1", ex=48 * 60 * 60)
    await redis.set("leaguemates:daily_sync:last_run", "1", ex=24 * 60 * 60)

    return {
        "status": "enqueued",
        "active_users_count": len(active_usernames),
        "usernames": active_usernames,
        "date": today_str,
    }


