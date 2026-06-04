from taskiq import TaskiqEvents, TaskiqState

from app.core.broker import broker
from app.core.logger import setup_logging
from app.integrations.sleeper.singleton import get_worker_sleeper_client

setup_logging()

@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: TaskiqState):
    state.sleeper = get_worker_sleeper_client()

@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown(state: TaskiqState):
    sleeper = getattr(state, "sleeper", None)
    if sleeper:
        await sleeper.close()