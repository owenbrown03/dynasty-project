import httpx, asyncio


class HTTPClientManager:
    _client: httpx.AsyncClient | None = None
    _lock = asyncio.Lock()

    @classmethod
    async def get(cls) -> httpx.AsyncClient:
        if cls._client is None:
            async with cls._lock:
                if cls._client is None:
                    cls._client = httpx.AsyncClient(
                        timeout=httpx.Timeout(30.0, connect=5.0),
                        limits=httpx.Limits(
                            max_connections=200,
                            max_keepalive_connections=50,
                        ),
                    )
        return cls._client

    @classmethod
    async def close(cls):
        if cls._client:
            await cls._client.aclose()
            cls._client = None