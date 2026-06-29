from app.analytics.war.models import (
    PlayerProjectionValue,
    PlayerWAR,
)


class WARCalculator:

    def calculate(
        self,
        players: list[PlayerProjectionValue],
        replacement_values: dict[str, float],
    ) -> list[PlayerWAR]:

        results = []

        for player in players:

            replacement = replacement_values.get(
                player.position,
                0,
            )

            war = max(
                player.projected_points - replacement,
                0,
            )

            war_per_game = war / 17

            results.append(
                PlayerWAR(
                    player_id=player.player_id,
                    name=player.name,
                    position=player.position,
                    team=player.team,

                    projected_points=(
                        player.projected_points
                    ),

                    replacement_points=(
                        replacement
                    ),

                    war=war,
                    war_per_game=war_per_game,
                )
            )

        return sorted(
            results,
            key=lambda x: x.war,
            reverse=True,
        )