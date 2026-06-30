from .models import ExpectedGamesRemaining
from .tables import EXPECTED_YEARS_REMAINING
from ..constants import FANTASY_GAMES_PER_SEASON

class ExpectedGamesRemainingService:

    def calculate(
        self,
        age: float,
        position: str,
    ) -> ExpectedGamesRemaining:

        position_table = EXPECTED_YEARS_REMAINING[position]

        lower_age = int(age)
        upper_age = lower_age + 1

        if lower_age not in position_table:
            lower_age = min(position_table.keys())

        if upper_age not in position_table:
            upper_age = max(position_table.keys())

        lower_years = position_table[lower_age]
        upper_years = position_table[upper_age]

        fraction = age - lower_age

        years_remaining = (
            lower_years +
            (
                upper_years -
                lower_years
            ) * fraction
        )

        games_remaining = (
            years_remaining *
            FANTASY_GAMES_PER_SEASON
        )

        return ExpectedGamesRemaining(
            age=age,
            position=position,
            years_remaining=years_remaining,
            games_remaining=games_remaining,
        )