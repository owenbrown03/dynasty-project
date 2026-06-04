import importlib, pkgutil, logging
from taskiq_redis import ListQueueBroker

import app.tasks as tasks_pkg

broker = ListQueueBroker("redis://redis:6379")
logger = logging.getLogger(__name__)

for _, name, _ in pkgutil.iter_modules(tasks_pkg.__path__, tasks_pkg.__name__ + "."):
    try:
        importlib.import_module(name)
        logger.info(f"Loaded task module: {name}")
    except Exception:
        logger.exception(f"Failed to load task module: {name}")
        raise