import asyncio

from .client import SleeperClient
from .config import SleeperConfig
from .http import HTTPTransport
from .limiter import TokenBucket

from app.integrations.http.manager import HTTPClientManager


class SleeperClientManager:
    _client: SleeperClient | None = None
    _lock = asyncio.Lock()

    @classmethod
    async def get(cls) -> SleeperClient:
        if cls._client is None:
            async with cls._lock:
                if cls._client is None:

                    http_client = await HTTPClientManager.get()

                    cls._client = SleeperClient(
                        http=HTTPTransport(http_client),
                        limiter=TokenBucket(
                            rate=100,
                            per=1.0,
                        ),
                        config=SleeperConfig(),
                    )

        return cls._client