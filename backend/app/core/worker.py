import asyncio
import logging
from contextlib import suppress

from taskiq import TaskiqEvents, TaskiqState

from app.core.broker import broker
from app.infrastructure.http.manager import HTTPClientManager
from app.infrastructure.redis.manager import RedisManager
from app.integrations.sleeper.singleton import get_worker_sleeper_client
from app.core.logger import setup_logging
from app.tasks.maintenance import run_daily_external_syncs_task
from app.tasks.reminders import send_due_reminder_emails_task
from app.tasks.user import sync_active_users_current_season_task
from app.tasks.trade import run_daily_leaguemate_syncs_task

setup_logging()

logger = logging.getLogger(__name__)

DAILY_EXTERNAL_SYNC_CHECK_INTERVAL_SECONDS = 30 * 60

SCHEDULER_LEADER_KEY = "sync:scheduler:leader"
SCHEDULER_LEADER_TTL_SECONDS = 30 * 60


async def acquire_scheduler_leader() -> str | None:
    redis = await RedisManager.get()
    import uuid

    token = uuid.uuid4().hex

    acquired = await redis.set(
        SCHEDULER_LEADER_KEY,
        token,
        ex=SCHEDULER_LEADER_TTL_SECONDS,
        nx=True,
    )

    if acquired:
        return token

    return None


async def release_scheduler_leader(token: str) -> None:
    redis = await RedisManager.get()
    current = await redis.get(SCHEDULER_LEADER_KEY)

    if current == token:
        await redis.delete(SCHEDULER_LEADER_KEY)


async def refresh_scheduler_leader(token: str) -> bool:
    redis = await RedisManager.get()
    current = await redis.get(SCHEDULER_LEADER_KEY)

    if current != token:
        return False

    await redis.expire(
        SCHEDULER_LEADER_KEY,
        SCHEDULER_LEADER_TTL_SECONDS,
    )

    return True


async def enqueue_daily_external_sync_checks(token: str):
    while True:
        alive = await refresh_scheduler_leader(token)

        if not alive:
            logger.info(
                "Scheduler leader lock lost; stopping scheduling loop",
            )
            break

        await sync_active_users_current_season_task.kiq()
        await run_daily_leaguemate_syncs_task.kiq()
        await run_daily_external_syncs_task.kiq()
        await send_due_reminder_emails_task.kiq()
        await asyncio.sleep(
            DAILY_EXTERNAL_SYNC_CHECK_INTERVAL_SECONDS,
        )


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: TaskiqState):
    state.sleeper = await get_worker_sleeper_client()

    leader_token = await acquire_scheduler_leader()

    if leader_token is None:
        logger.info(
            "Another worker is the scheduler leader; skipping scheduling loop",
        )
        state.daily_external_sync_scheduler = None
        state.scheduler_leader_token = None
        return

    logger.info("Acquired scheduler leader lock")
    state.scheduler_leader_token = leader_token
    state.daily_external_sync_scheduler = asyncio.create_task(
        enqueue_daily_external_sync_checks(leader_token),
    )


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown(state: TaskiqState):
    scheduler = getattr(
        state,
        "daily_external_sync_scheduler",
        None,
    )

    if scheduler is not None:
        scheduler.cancel()
        with suppress(asyncio.CancelledError):
            await scheduler

    leader_token = getattr(
        state,
        "scheduler_leader_token",
        None,
    )

    if leader_token is not None:
        await release_scheduler_leader(leader_token)
        logger.info("Released scheduler leader lock")

    await HTTPClientManager.close()
