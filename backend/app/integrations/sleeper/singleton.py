from app.integrations.sleeper.client import SleeperClient

_sleeper_client: SleeperClient | None = None


def get_worker_sleeper_client() -> SleeperClient:
    global _sleeper_client

    if _sleeper_client is None:
        _sleeper_client = SleeperClient()

    return _sleeper_client