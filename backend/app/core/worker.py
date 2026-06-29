from taskiq import TaskiqEvents, TaskiqState

from app.core.broker import broker
from app.infrastructure.http.manager import HTTPClientManager
from app.integrations.sleeper.singleton import get_worker_sleeper_client
from app.core.logger import setup_logging

setup_logging()


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: TaskiqState):
    state.sleeper = await get_worker_sleeper_client()


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown(state: TaskiqState):
    await HTTPClientManager.close()