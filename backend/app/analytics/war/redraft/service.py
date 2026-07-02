import logging

from sqlalchemy.ext.asyncio import AsyncSession

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

logger = logging.getLogger(__name__)


class WARService:

    def __init__(self):

        self.loader = PlayerValueLoader()

        self.scoring_calculator = FantasyScoringCalculator()

        self.merger = WARMerger()
        
        self.normalizer = PlayerNormalizer(
            self.scoring_calculator
        )

        self.starter_pool = (
            StarterPoolCalculator()
        )

        self.environment_calculator = (
            LeagueEnvironmentCalculator(
                self.starter_pool
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

        self.war_calculator = (
            WARCalculator(
                WinProbabilityCalculator()
            )
        )


    async def calculate(
        self,
        db: AsyncSession,
        league_id: str,
    ):

        logger.info(
            f"Starting WAR calculation for league {league_id}"
        )


        # -----------------------------------------
        # Load league data
        # -----------------------------------------

        league = await self.loader.get_league(
            db,
            league_id,
        )


        projections = await self.loader.get_projections(
            db,
            int(league.season),
        )


        players = await self.loader.get_players(
            db,
        )


        logger.info(
            f"""
            League Loaded

            name={league.name}
            season={league.season}
            teams={league.total_rosters}
            """
        )


        # -----------------------------------------
        # Normalize projections
        # -----------------------------------------

        normalized = (
            self.normalizer.normalize(
                projections=projections,
                players=players,
                scoring_settings=league.scoring_settings,
                roster_positions=league.roster_positions,
            )
        )


        logger.info(
            f"Normalized players: {len(normalized)}"
        )


        # -----------------------------------------
        # League environment
        # -----------------------------------------

        environment = (
            self.environment_calculator.calculate(
                players=normalized,
                roster_positions=league.roster_positions,
                teams=league.total_rosters,
            )
        )


        # -----------------------------------------
        # Starter WAR
        # -----------------------------------------

        starter_replacement_values = (
            self.replacement_calculator.calculate(
                players=normalized,
                roster_positions=league.roster_positions,
                total_rosters=league.total_rosters,
            )
        )


        starter_results = (
            self.war_calculator.calculate(
                players=normalized,
                replacement_values=starter_replacement_values,
                environment=environment,
            )
        )


        # -----------------------------------------
        # Roster WAR
        # -----------------------------------------

        replacement_roster = (
            self.replacement_roster_builder.build(
                players=normalized,
                roster_positions=league.roster_positions,
                total_rosters=league.total_rosters,
            )
        )


        bench_replacement_values = (
            self.bench_replacement_calculator.calculate(
                players=normalized,
                replacement_roster=replacement_roster,
            )
        )


        roster_results = (
            self.war_calculator.calculate(
                players=normalized,
                replacement_values=bench_replacement_values,
                environment=environment,
            )
        )


        # -----------------------------------------
        # Merge Starter WAR + Roster WAR
        # -----------------------------------------

        results = self.merger.merge(
            starter_results=starter_results,
            roster_results=roster_results,
        )


        logger.info(
            f"WAR calculated for {len(results)} players"
        )


        return results