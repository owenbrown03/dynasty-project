import logging
from typing import Any
from redis.asyncio import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def get(self, key: str) -> Any | None:
        try:
            return await self.redis.get(key)
        except RedisError as exc:
            logger.warning("Redis get error for key %s: %s", key, exc)
            return None

    async def mget(
        self,
        keys: list[str],
    ) -> list[Any | None]:
        if not keys:
            return []

        try:
            return await self.redis.mget(keys)
        except RedisError as exc:
            logger.warning("Redis mget error: %s", exc)
            return [None] * len(keys)

    async def set(
        self,
        key: str,
        value: str,
        ttl_seconds: int | None = None,
    ) -> bool:
        try:
            await self.redis.set(
                key,
                value,
                ex=ttl_seconds,
            )
            return True
        except RedisError as exc:
            logger.warning("Redis set error for key %s: %s", key, exc)
            return False

    async def delete(self, key: str) -> None:
        try:
            await self.redis.delete(key)
        except RedisError as exc:
            logger.warning("Redis delete error for key %s: %s", key, exc)

    async def delete_prefix(
        self,
        prefix: str,
    ) -> None:
        try:
            keys: list[str] = []
            async for key in self.redis.scan_iter(
                match=f"{prefix}*",
            ):
                keys.append(key)

            if keys:
                await self.redis.delete(*keys)
        except RedisError as exc:
            logger.warning("Redis delete_prefix error for prefix %s: %s", prefix, exc)

    async def incr_with_ttl(
        self,
        key: str,
        ttl_seconds: int,
    ) -> int:
        try:
            value = await self.redis.incr(key)

            if value == 1:
                await self.redis.expire(
                    key,
                    ttl_seconds,
                )

            return value
        except RedisError as exc:
            logger.warning("Redis incr error for key %s: %s", key, exc)
            return 1
