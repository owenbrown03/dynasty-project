from taskiq import TaskiqEvents, TaskiqState

from app.services import sleeper
from app.core.broker import broker
from app.core.logger import setup_logging
setup_logging() 

@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: TaskiqState):
    if not sleeper.client:
        await sleeper.open_client()

@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown(state: TaskiqState):
    if sleeper.client:
        await sleeper.close_client()