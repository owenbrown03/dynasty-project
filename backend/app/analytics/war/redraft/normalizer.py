from app.utils.age import calculate_age
from .constants import FANTASY_GAMES_PER_SEASON
from .models import PlayerProjectionValue

class PlayerNormalizer:

    def __init__(self, scoring_calculator):
        self.scoring_calculator = scoring_calculator


    def normalize(
        self,
        projections,
        players,
        scoring_settings,
        roster_positions,
    ):

        normalized = []

        for projection in projections:

            player = players.get(
                projection.player_id
            )

            if not player:
                continue

            if (
                not player.position
                or player.position not in roster_positions
            ):
                continue

            stats = projection.to_stats()

            games_played = int(
                projection.games_played
                or FANTASY_GAMES_PER_SEASON
            )

            projected_points = (
                self.scoring_calculator.calculate(
                    stats,
                    scoring_settings,
                )
            )

            normalized.append(
                PlayerProjectionValue(
                    player_id=projection.player_id,
                    name=player.full_name,
                    position=player.position,
                    team=player.team,
                    age=calculate_age(
                        player.birth_date
                    ),
                    stats=stats,
                    games_played=games_played,
                    projected_points=projected_points,
                    projected_ppg=(
                        projected_points /
                        games_played
                    ),
                )
            )

        return normalized