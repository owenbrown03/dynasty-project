from .constants import FANTASY_GAMES_PER_SEASON
from .models import LeagueEnvironment, PlayerProjectionValue
from .starter_pool import StarterPoolCalculator


class LeagueEnvironmentCalculator:

    def __init__(
        self,
        starter_calculator: StarterPoolCalculator,
    ):
        self.starter_calculator = starter_calculator


    def calculate(
        self,
        players: list[PlayerProjectionValue],
        roster_positions: list[str],
        teams: int,
        weeks: int = FANTASY_GAMES_PER_SEASON,
    ) -> LeagueEnvironment:

        starting_slots = len(
            [
                x
                for x in roster_positions
                if x not in {"BN", "IR", "TAXI"}
            ]
        )

        total_starter_slots = (
            teams * starting_slots
        )

        starters = self.starter_calculator.select(
            players,
            roster_positions,
            teams,
        )

        total_points = sum(
            p.projected_points
            for p in starters
        )
        
        average_team_points = (
                total_points /
                teams
            )
        
        average_team_ppg=(
            average_team_points / weeks
        )

        return LeagueEnvironment(
            teams=teams,
            starting_slots=starting_slots,
            total_starter_slots=total_starter_slots,
            average_team_points=average_team_points,
            average_team_ppg=average_team_ppg,
            scoring_std_dev=25.0, #replace later with historical data
            weeks=weeks,
            replacement_points={},
        )