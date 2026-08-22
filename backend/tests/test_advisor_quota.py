import asyncio
import json
from datetime import datetime, timezone

import pytest

from app.core.config import settings
from app.services.advisor import quota
from app.infrastructure.redis.client import RedisClient


class FakeRedisBackend:
    def __init__(self):
        self.store: dict = {}
        self.ttls: dict = {}

    async def incr(self, key: str) -> int:
        self.store[key] = self.store.get(key, 0) + 1
        return self.store[key]

    async def decr(self, key: str) -> int:
        self.store[key] = self.store.get(key, 0) - 1
        return self.store[key]

    async def expire(self, key: str, ttl: int):
        self.ttls[key] = ttl

    async def set(self, key: str, value, ex=None):
        self.store[key] = value


class FakeRedis(RedisClient):
    def __init__(self):
        self.backend = FakeRedisBackend()

        class _Inner:
            def __init__(self, backend):
                self._backend = backend

            def __getattr__(self, name):
                return getattr(self._backend, name)

        super().__init__(_Inner(self.backend))

    async def get(self, key):
        return self.backend.store.get(key)

    async def incr_with_ttl(self, key: str, ttl_seconds: int) -> int:
        value = await self.backend.incr(key)
        if value == 1:
            await self.backend.expire(key, ttl_seconds)
        return value

    async def set(self, key, value, ttl_seconds=None):
        await self.backend.set(key, value)


@pytest.fixture
def fake_redis():
    return FakeRedis()


def test_consume_quota_allows_under_limit(fake_redis):
    async def run():
        for _ in range(settings.GEMINI_RPM_LIMIT):
            await quota.consume_quota(fake_redis)

    asyncio.run(run())


def test_consume_quota_rejects_over_minute_limit(fake_redis, monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_RPM_LIMIT", 2)

    async def run():
        await quota.consume_quota(fake_redis)
        await quota.consume_quota(fake_redis)

        with pytest.raises(quota.GeminiQuotaExceeded, match="minute"):
            await quota.consume_quota(fake_redis)

    asyncio.run(run())


def test_consume_quota_rejects_over_daily_limit(fake_redis, monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_DAILY_LIMIT", 3)

    async def run():
        for _ in range(3):
            await quota.consume_quota(fake_redis)

        with pytest.raises(quota.GeminiQuotaExceeded, match="daily"):
            await quota.consume_quota(fake_redis)

    asyncio.run(run())


def test_refund_quota_decrements_counters(fake_redis, monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_RPM_LIMIT", 1)

    minute_key = quota._minute_key(quota.datetime.now(timezone.utc))

    async def run():
        await quota.consume_quota(fake_redis)
        assert fake_redis.backend.store[minute_key] == 1

        await quota.refund_quota(fake_redis)
        assert fake_redis.backend.store[minute_key] == 0

        await quota.consume_quota(fake_redis)

    asyncio.run(run())


def test_generation_cache_roundtrip(fake_redis):
    payload = {"cards": [{"headline": "Buy low"}]}

    async def run():
        cached = await quota.get_cached_generation(
            fake_redis,
            model="m",
            system_instruction="sys",
            prompt="p",
        )
        assert cached is None

        await quota.cache_generation(
            fake_redis,
            model="m",
            system_instruction="sys",
            prompt="p",
            payload=payload,
        )

        return await quota.get_cached_generation(
            fake_redis,
            model="m",
            system_instruction="sys",
            prompt="p",
        )

    assert asyncio.run(run()) == payload


def test_cache_key_depends_on_prompt(fake_redis):
    async def run():
        await quota.cache_generation(
            fake_redis,
            model="m",
            system_instruction="s",
            prompt="prompt-a",
            payload={"v": 1},
        )

        return await quota.get_cached_generation(
            fake_redis,
            model="m",
            system_instruction="s",
            prompt="prompt-b",
        )

    assert asyncio.run(run()) is None


def test_cache_key_shape():
    key = quota.build_cache_key(
        model="m",
        system_instruction="s",
        prompt=json.dumps({"a": 1}),
    )

    assert key.startswith("gemini:cache:")
