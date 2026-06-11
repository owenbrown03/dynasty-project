from redis.asyncio import Redis


class RedisClient:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def get(self, key: str):
        return await self.redis.get(key)

    async def set(
        self,
        key: str,
        value: str,
        ttl_seconds: int | None = None,
    ):
        await self.redis.set(
            key,
            value,
            ex=ttl_seconds,
        )

    async def delete(self, key: str):
        await self.redis.delete(key)