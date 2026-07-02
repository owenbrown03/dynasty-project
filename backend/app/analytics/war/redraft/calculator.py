import logging

from .models import (
    PlayerProjectionValue,
    CalculatedWAR,
    LeagueEnvironment,
)

logger = logging.getLogger(__name__)


class WARCalculator:

    VERSION = "2.0"


    def __init__(
        self,
        win_calculator,
    ):
        self.win_calculator = win_calculator


    def calculate(
        self,
        players: list[PlayerProjectionValue],
        replacement_values: dict[str, float],
        environment: LeagueEnvironment,
    ) -> list[CalculatedWAR]:

        results = []

        for player in players:

            replacement_points = replacement_values.get(
                player.position
            )

            if replacement_points is None:
                continue


            war = self.win_calculator.calculate(
                player_points=player.projected_points,
                replacement_points=replacement_points,
                environment=environment,
            )


            war_per_game = (
                war / player.games_played
                if player.games_played
                else 0
            )


            results.append(
                CalculatedWAR(
                    player_id=player.player_id,
                    name=player.name,
                    position=player.position,
                    team=player.team,
                    age=player.age,

                    projection=player.projected_points,
                    replacement=replacement_points,

                    war=war,
                    war_per_game=war_per_game,

                    model_version=self.VERSION,
                )
            )


        return sorted(
            results,
            key=lambda x: x.war,
            reverse=True,
        )