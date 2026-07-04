import json

from app.infrastructure.redis.client import RedisClient
from .constants import WAR_CACHE_VERSION, WAR_CACHE_TTL_SECONDS
from .models import PlayerWAR


class WARCache:

    def _league_key(
        self,
        league_id: str,
        season: int,
    ) -> str:
        return (
            f"war:{WAR_CACHE_VERSION}:league:"
            f"{league_id}:{season}"
        )

    async def get_league(
        self,
        redis: RedisClient,
        league_id: str,
        season: int,
    ) -> list[PlayerWAR] | None:

        cached = await redis.get(
            self._league_key(
                league_id,
                season,
            )
        )

        if cached is None:
            return None

        data = json.loads(cached)

        return [
            PlayerWAR(**item)
            for item in data
        ]

    async def set_league(
        self,
        redis: RedisClient,
        league_id: str,
        season: int,
        value: list[PlayerWAR],
    ):

        await redis.set(
            self._league_key(
                league_id,
                season,
            ),
            json.dumps(
                [
                    p.model_dump()
                    for p in value
                ]
            ),
            ttl_seconds=WAR_CACHE_TTL_SECONDS,
        )

    async def clear_league(
        self,
        redis: RedisClient,
        league_id: str,
        season: int,
    ):

        await redis.delete(
            self._league_key(
                league_id,
                season,
            )
        )


war_cache = WARCache()