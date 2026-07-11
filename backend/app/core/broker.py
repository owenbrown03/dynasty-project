import importlib
import logging
import pkgutil

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


def iter_task_module_names(
    package=tasks_pkg,
) -> list[str]:
    return [
        name
        for _, name, _ in pkgutil.iter_modules(
            package.__path__,
            package.__name__ + ".",
        )
    ]


def load_task_modules(
    package=tasks_pkg,
) -> None:
    for name in iter_task_module_names(package):
        try:
            importlib.import_module(name)
            logger.info(
                "Loaded task module: %s",
                name,
            )
        except Exception:
            logger.exception(
                "Failed to load task module: %s",
                name,
            )
            raise


load_task_modules()
