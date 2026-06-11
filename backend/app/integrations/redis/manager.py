from redis.asyncio import Redis

from app.core.config import settings


class RedisManager:
    _client: Redis | None = None

    @classmethod
    async def get(cls) -> Redis:
        if cls._client is None:
            cls._client = Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )

            await cls._client.ping()

        return cls._client

    @classmethod
    async def close(cls):
        if cls._client:
            await cls._client.aclose()
            cls._client = None