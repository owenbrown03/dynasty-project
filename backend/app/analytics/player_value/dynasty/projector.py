from dataclasses import dataclass

from ..constants import FANTASY_GAMES_PER_SEASON
from .aging import AgingCurve
from .discount import DiscountCurve
from .expected_games import ExpectedGamesRemainingService


@dataclass
class FutureWAR:
    future_war: float
    expected_games: float
    seasons_remaining: float
    career_multiplier: float | None = None

@dataclass
class DynastyWAR:
    current_war: float
    future_war: float
    total_war: float
    expected_games: float
    seasons_remaining: float
    career_multiplier: float | None = None

class WARProjector:
    """
    Converts current player WAR into dynasty-adjusted future WAR.

    Responsibilities:
    - determine future game horizon
    - apply aging curve
    - apply dynasty discount curve
    - aggregate future value
    """
    
    def __init__(
        self,
        expected_games_service: ExpectedGamesRemainingService,
        aging_curve: AgingCurve,
        discount_curve: DiscountCurve,
    ):
        self.expected_games_service = expected_games_service
        self.aging_curve = aging_curve
        self.discount_curve = discount_curve

    def project(
        self,
        *,
        war: float,
        age: float,
        position: str,
    ) -> FutureWAR:
        """
        Project dynasty-adjusted WAR.

        Args:
            war:
                Current player WAR baseline.

            age:
                Current player age.

            position:
                Fantasy position.

        Returns:
            FutureWAR projection.
        """

        expected_games = self.expected_games_service.calculate(
            age=age,
            position=position,
        ).games_remaining

        total_war = 0.0

        for game in range(1, int(expected_games) + 1):
            future_age = age + (game / FANTASY_GAMES_PER_SEASON)

            aging_multiplier = self.aging_curve.multiplier(
                age=future_age,
                position=position,
            )

            discount_multiplier = self.discount_curve.multiplier(
                games_from_now=game,
            )

            total_war += (
                war
                * aging_multiplier
                * discount_multiplier
                / FANTASY_GAMES_PER_SEASON
            )

        seasons_remaining = expected_games / FANTASY_GAMES_PER_SEASON

        war_multiplier = None

        if war > 0:
            war_multiplier = total_war / war

        return FutureWAR(
            future_war=total_war,
            expected_games=expected_games,
            seasons_remaining=seasons_remaining,
            career_multiplier=war_multiplier,
        )