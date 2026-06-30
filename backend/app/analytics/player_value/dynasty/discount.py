import math

from ..constants import FANTASY_GAMES_PER_SEASON

class DiscountCurve:

    def __init__(
        self,
        annual_discount_rate: float = 0.15,
        games_per_season: int = FANTASY_GAMES_PER_SEASON,
    ):
        self.annual_discount_rate = annual_discount_rate
        self.games_per_season = games_per_season


    def multiplier(
        self,
        games_from_now: float,
    ) -> float:

        years = (
            games_from_now /
            self.games_per_season
        )

        return math.exp(
            -self.annual_discount_rate * years
        )