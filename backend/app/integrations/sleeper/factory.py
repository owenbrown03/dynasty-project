from app.infrastructure.http.manager import HTTPClientManager
from app.infrastructure.http.transport import HTTPTransport

from .auth import SleeperAuth
from .client import SleeperClient
from .config import SleeperConfig
from .limiter import TokenBucket
from .transport import SleeperTransport


async def get_sleeper_client(
    token: str | None = None,
) -> SleeperClient:

    config = SleeperConfig()

    http_client = await HTTPClientManager.get()

    http = HTTPTransport(
        http_client
    )

    limiter = TokenBucket(
        capacity=config.rate_limit_capacity,
        refill_rate=config.rate_limit_refill,
    )

    auth = SleeperAuth(
        token
    )

    transport = SleeperTransport(
        auth=auth,
        http=http,
        limiter=limiter,
        config=config,
    )

    return SleeperClient(
        transport=transport,
        auth=auth,
        limiter=limiter,
        config=config,
    )