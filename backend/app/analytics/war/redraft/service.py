import json
from dataclasses import dataclass

from cachetools import LRUCache
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.redis.client import RedisClient

from .cache import war_cache
from .loader import PlayerValueLoader
from .normalizer import PlayerNormalizer
from .replacement import (
    ReplacementCalculator,
    ReplacementRosterBuilder,
    BenchReplacementCalculator,
)
from .calculator import WARCalculator
from .environment import LeagueEnvironmentCalculator
from .starter_pool import StarterPoolCalculator
from .win_probability import WinProbabilityCalculator
from .scoring import FantasyScoringCalculator
from .merger import WARMerger


@dataclass
class WARSharedData:
    players: dict
    projections: list


class WARService:

    def __init__(self):

        self._normalization_cache = LRUCache(maxsize=128)

        self.loader = PlayerValueLoader()

        self.scoring_calculator = FantasyScoringCalculator()
        self.normalizer = PlayerNormalizer(
            self.scoring_calculator,
        )

        self.starter_pool = StarterPoolCalculator()

        self.environment_calculator = (
            LeagueEnvironmentCalculator(
                self.starter_pool,
            )
        )

        self.replacement_calculator = (
            ReplacementCalculator()
        )

        self.replacement_roster_builder = (
            ReplacementRosterBuilder()
        )

        self.bench_replacement_calculator = (
            BenchReplacementCalculator()
        )

        self.war_calculator = WARCalculator(
            WinProbabilityCalculator()
        )

        self.merger = WARMerger()

    async def load_shared_data(
        self,
        db,
        season,
    ):

        projections = await self.loader.get_projections(
            db,
            season,
        )

        players = await self.loader.get_players(
            db,
        )

        return WARSharedData(
            players=players,
            projections=projections,
        )

    async def calculate(
        self,
        db: AsyncSession,
        redis: RedisClient,
        league_id: str,
    ):

        league = await self.loader.get_league(
            db,
            league_id,
        )

        cached = await war_cache.get_league(
            redis,
            league_id,
            league.season,
        )

        if cached is not None:
            return cached

        shared = await self.load_shared_data(
            db,
            league.season,
        )

        results = await self.calculate_with_data(
            league,
            shared,
        )

        await war_cache.set_league(
            redis,
            league_id,
            league.season,
            results,
        )

        return results

    async def calculate_with_data(
        self,
        league,
        shared: WARSharedData,
    ):

        cache_key = (
            league.season,
            json.dumps(
                league.scoring_settings,
                sort_keys=True,
            ),
            json.dumps(
                league.roster_positions,
                sort_keys=True,
            ),
            league.total_rosters,
        )

        normalized = self._normalization_cache.get(
            cache_key,
        )

        if normalized is None:

            normalized = self.normalizer.normalize(
                projections=shared.projections,
                players=shared.players,
                scoring_settings=league.scoring_settings,
                roster_positions=league.roster_positions,
            )

            self._normalization_cache[
                cache_key
            ] = normalized

        environment = (
            self.environment_calculator.calculate(
                players=normalized,
                roster_positions=league.roster_positions,
                teams=league.total_rosters,
            )
        )

        starter_replacement = (
            self.replacement_calculator.calculate(
                players=normalized,
                roster_positions=league.roster_positions,
                total_rosters=league.total_rosters,
            )
        )

        bench_replacement = (
            self.bench_replacement_calculator.calculate(
                players=normalized,
                replacement_roster=self.replacement_roster_builder.build(
                    players=normalized,
                    roster_positions=league.roster_positions,
                    total_rosters=league.total_rosters,
                ),
            )
        )

        starter_results = self.war_calculator.calculate(
            players=normalized,
            replacement_values=starter_replacement,
            environment=environment,
        )

        roster_results = self.war_calculator.calculate(
            players=normalized,
            replacement_values=bench_replacement,
            environment=environment,
        )

        return self.merger.merge(
            starter_results=starter_results,
            roster_results=roster_results,
        )