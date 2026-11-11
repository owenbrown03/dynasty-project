import time
from sqlmodel import select

from app.models.db.sleeper.api import Player, League, PlayerProjection, PlayerSeasonStats

LOADER_CACHE_TTL_SECONDS = 1800  # 30 minutes


class PlayerValueLoader:

    def __init__(self, ttl_seconds: int = LOADER_CACHE_TTL_SECONDS):
        self._ttl = ttl_seconds
        self._season_stats_cache: dict[tuple[int, str], tuple[float, list[PlayerSeasonStats]]] = {}
        self._players_cache: tuple[float, dict[str, Player]] | None = None
        self._projections_cache: dict[int, tuple[float, list[PlayerProjection]]] = {}

    def clear_cache(self) -> None:
        self._season_stats_cache.clear()
        self._players_cache = None
        self._projections_cache.clear()

    async def get_league(
        self,
        db,
        league_id,
    ):
        league = await db.get(
            League,
            league_id,
        )

        if not league:
            raise ValueError(
                f"League {league_id} not found"
            )

        return league

    async def get_projections(
        self,
        db,
        season,
    ):
        now = time.monotonic()
        if season in self._projections_cache:
            cached_at, data = self._projections_cache[season]
            if now - cached_at < self._ttl:
                return data

        result = await db.execute(
            select(PlayerProjection)
            .where(
                PlayerProjection.season == season
            )
        )

        rows = list(result.scalars().all())
        self._projections_cache[season] = (now, rows)
        return rows

    async def get_season_stats(
        self,
        db,
        season,
        *,
        season_type: str = "regular",
    ):
        now = time.monotonic()
        cache_key = (season, season_type)
        if cache_key in self._season_stats_cache:
            cached_at, data = self._season_stats_cache[cache_key]
            if now - cached_at < self._ttl:
                return data

        result = await db.execute(
            select(PlayerSeasonStats)
            .where(
                PlayerSeasonStats.season == season,
                PlayerSeasonStats.season_type == season_type,
            )
        )

        rows = list(result.scalars().all())
        self._season_stats_cache[cache_key] = (now, rows)
        return rows

    async def get_players(
        self,
        db,
    ):
        now = time.monotonic()
        if self._players_cache is not None:
            cached_at, data = self._players_cache
            if now - cached_at < self._ttl:
                return data

        result = await db.execute(
            select(Player)
        )

        players = {
            p.player_id: p
            for p in result.scalars()
        }
        self._players_cache = (now, players)
        return players

