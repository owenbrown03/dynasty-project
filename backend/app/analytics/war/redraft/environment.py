from dataclasses import dataclass
import logging
import statistics

from .starter_pool import StarterPoolCalculator
from .models import PlayerProjectionValue
from .constants import FANTASY_GAMES_PER_SEASON

logger = logging.getLogger(__name__)


@dataclass
class LeagueEnvironment:
    teams: int
    weeks: int
    starter_count: int
    total_points: float
    average_team_ppg: float
    scoring_std_dev: float


class LeagueEnvironmentCalculator:

    def __init__(
        self,
        starter_pool: StarterPoolCalculator,
    ):
        self.starter_pool = starter_pool


    def calculate(
        self,
        players: list[PlayerProjectionValue],
        roster_positions: list[str],
        teams: int,
    ) -> LeagueEnvironment:

        starters = self.starter_pool.select(
            players=players,
            roster_positions=roster_positions,
            teams=teams,
        )


        starter_points = [
            p.projected_points
            for p in starters
        ]


        total_points = sum(starter_points)

        starter_count = len(starter_points)


        # Average team weekly scoring environment
        average_team_ppg = (
            total_points /
            teams /
            FANTASY_GAMES_PER_SEASON
            if teams
            else 0
        )


        scoring_std_dev = (
            statistics.stdev(starter_points)
            if len(starter_points) > 1
            else 0
        )


        environment = LeagueEnvironment(
            teams=teams,
            weeks=FANTASY_GAMES_PER_SEASON,
            starter_count=starter_count,
            total_points=total_points,
            average_team_ppg=average_team_ppg,
            scoring_std_dev=scoring_std_dev,
        )


        logger.debug(
            f"""
            League Environment:

            teams={environment.teams}
            weeks={environment.weeks}
            starters={environment.starter_count}
            total_points={environment.total_points:.2f}
            avg_team_ppg={environment.average_team_ppg:.2f}
            scoring_std_dev={environment.scoring_std_dev:.2f}
            """
        )


        return environment