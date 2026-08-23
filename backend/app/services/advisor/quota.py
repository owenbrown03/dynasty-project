import hashlib
import json
from datetime import datetime, timezone

from app.core.config import settings
from app.infrastructure.redis.client import RedisClient


class GeminiQuotaExceeded(Exception):
    def __init__(self, scope: str):
        self.scope = scope
        super().__init__(
            f"Gemini quota exceeded for scope: {scope}"
        )


MINUTE_WINDOW_SECONDS = 60
DAY_TTL_SECONDS = 172800


def _minute_key(now: datetime) -> str:
    return (
        f"gemini:quota:min:"
        f"{now.strftime('%Y%m%d%H%M')}"
    )


def _day_key(now: datetime) -> str:
    return f"gemini:quota:day:{now.strftime('%Y%m%d')}"


async def consume_quota(
    redis: RedisClient,
    *,
    user_id: int | None = None,
) -> None:
    now = datetime.now(timezone.utc)

    minute_count = await redis.incr_with_ttl(
        _minute_key(now),
        MINUTE_WINDOW_SECONDS,
    )

    if minute_count > settings.GEMINI_RPM_LIMIT:
        raise GeminiQuotaExceeded("minute")

    day_count = await redis.incr_with_ttl(
        _day_key(now),
        DAY_TTL_SECONDS,
    )

    if day_count > settings.GEMINI_DAILY_LIMIT:
        raise GeminiQuotaExceeded("daily")


async def refund_quota(
    redis: RedisClient,
) -> None:
    now = datetime.now(timezone.utc)

    minute_value = await redis.get(_minute_key(now))
    if minute_value is not None and int(minute_value) > 0:
        await redis.redis.decr(_minute_key(now))

    day_value = await redis.get(_day_key(now))
    if day_value is not None and int(day_value) > 0:
        await redis.redis.decr(_day_key(now))


def build_cache_key(
    *,
    model: str,
    system_instruction: str,
    prompt: str,
) -> str:
    fingerprint = hashlib.sha256(
        f"{model}\n{system_instruction}\n{prompt}".encode()
    ).hexdigest()

    return f"gemini:cache:{fingerprint}"


async def get_cached_generation(
    redis: RedisClient,
    *,
    model: str,
    system_instruction: str,
    prompt: str,
) -> dict | None:
    cached = await redis.get(
        build_cache_key(
            model=model,
            system_instruction=system_instruction,
            prompt=prompt,
        )
    )

    if not cached:
        return None

    return json.loads(cached)


async def cache_generation(
    redis: RedisClient,
    *,
    model: str,
    system_instruction: str,
    prompt: str,
    payload: dict,
) -> None:
    await redis.set(
        build_cache_key(
            model=model,
            system_instruction=system_instruction,
            prompt=prompt,
        ),
        json.dumps(payload),
        ttl_seconds=settings.GEMINI_CACHE_TTL_SECONDS,
    )
