from redis.asyncio import Redis


class RedisClient:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def get(self, key: str):
        return await self.redis.get(key)

    async def mget(
        self,
        keys: list[str],
    ):
        if not keys:
            return []

        return await self.redis.mget(keys)

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

    async def delete_prefix(
        self,
        prefix: str,
    ):
        keys: list[str] = []
        async for key in self.redis.scan_iter(
            match=f"{prefix}*",
        ):
            keys.append(key)

        if keys:
            await self.redis.delete(*keys)
