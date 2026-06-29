import importlib
import pkgutil
import logging
from taskiq_redis import ListQueueBroker
import app.tasks as tasks_pkg
from app.core.config import settings

broker = ListQueueBroker(
    settings.REDIS_URL,
    queue_name="taskiq",
    max_connection_pool_size=10,
    socket_connect_timeout=5,
    socket_timeout=None,
    health_check_interval=30,
)

logger = logging.getLogger(__name__)


for _, name, _ in pkgutil.iter_modules(
    tasks_pkg.__path__,
    tasks_pkg.__name__ + ".",
):
    try:
        importlib.import_module(name)
        logger.info(f"Loaded task module: {name}")

    except Exception:
        logger.exception(
            f"Failed to load task module: {name}"
        )
        raise