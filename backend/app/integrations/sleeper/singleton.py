from .factory import get_sleeper_client

_sleeper = None


async def get_worker_sleeper_client():

    global _sleeper

    if _sleeper is None:
        _sleeper = await get_sleeper_client()

    return _sleeper