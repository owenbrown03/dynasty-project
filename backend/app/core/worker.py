import asyncio
from contextlib import suppress

from taskiq import TaskiqEvents, TaskiqState

from app.core.broker import broker
from app.infrastructure.http.manager import HTTPClientManager
from app.integrations.sleeper.singleton import get_worker_sleeper_client
from app.core.logger import setup_logging
from app.tasks.maintenance import run_daily_external_syncs_task
from app.tasks.reminders import send_due_reminder_emails_task

setup_logging()

DAILY_EXTERNAL_SYNC_CHECK_INTERVAL_SECONDS = 60 * 60


async def enqueue_daily_external_sync_checks():
    while True:
        await run_daily_external_syncs_task.kiq()
        await send_due_reminder_emails_task.kiq()
        await asyncio.sleep(
            DAILY_EXTERNAL_SYNC_CHECK_INTERVAL_SECONDS,
        )


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: TaskiqState):
    state.sleeper = await get_worker_sleeper_client()
    state.daily_external_sync_scheduler = asyncio.create_task(
        enqueue_daily_external_sync_checks(),
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

    await HTTPClientManager.close()
