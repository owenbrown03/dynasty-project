from .models import DynastyPlayerInput, DynastyProjection
from .projector import FutureWAR


class ProjectionMerger:

    def merge(
        self,
        *,
        player: DynastyPlayerInput,
        starter: FutureWAR,
        roster: FutureWAR,
    ) -> DynastyProjection:

        total_starter_war = (
            player.starter_war +
            starter.future_war
        )

        total_roster_war = (
            player.roster_war +
            roster.future_war
        )

        total_starter_multiplier = None
        if player.starter_war > 0:
            total_starter_multiplier = (
                total_starter_war /
                player.starter_war
            )

        total_roster_multiplier = None
        if player.roster_war > 0:
            total_roster_multiplier = (
                total_roster_war /
                player.roster_war
            )

        return DynastyProjection(
            player_id=player.player_id,
            name=player.name,
            position=player.position,
            team=player.team,
            age=player.age,

            current_starter_war=player.starter_war,
            current_roster_war=player.roster_war,

            future_starter_war=starter.future_war,
            future_roster_war=roster.future_war,

            total_starter_war=total_starter_war,
            total_roster_war=total_roster_war,

            total_starter_multiplier=total_starter_multiplier,
            total_roster_multiplier=total_roster_multiplier,

            expected_games_remaining=starter.expected_games,
            seasons_remaining=starter.seasons_remaining,
            career_multiplier=starter.career_multiplier,
        )