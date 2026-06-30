from .projector import WARProjector
from .models import DynastyProjection, DynastyPlayerInput


class DynastyWARService:

    def __init__(
        self,
        projector: WARProjector,
    ):
        self.projector = projector


    def project_player(
        self,
        player: DynastyPlayerInput,
    ) -> DynastyProjection:

        projection = self.projector.project(
            war=player.war,
            age=player.age,
            position=player.position,
        )

        total_war = (
            player.war +
            projection.future_war
        )
        
        total_multiplier = None
        if player.war > 0:
            total_multiplier = (
                total_war /
                player.war
            )

        return DynastyProjection(
            player_id=player.player_id,
            name=player.name,
            position=player.position,
            team=player.team,

            current_war=player.war,
            current_age=player.age,

            future_war=projection.future_war,
            total_war=total_war,

            expected_games_remaining=projection.expected_games,
            seasons_remaining=projection.seasons_remaining,
            
            career_multiplier=projection.career_multiplier,
            total_multiplier=total_multiplier,
        )