import pkgutil
import app.tasks as tasks_pkg
from taskiq_redis import ListQueueBroker

broker = ListQueueBroker("redis://redis:6379")

for _, name, _ in pkgutil.iter_modules(tasks_pkg.__path__, tasks_pkg.__name__ + "."):
    __import__(name)