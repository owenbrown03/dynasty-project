import logging

from .models import PlayerWAR

logger = logging.getLogger(__name__)


class WARMerger:

    def merge(
        self,
        starter_results,
        roster_results,
    ) -> list[PlayerWAR]:

        starter_by_id = {
            p.player_id: p
            for p in starter_results
        }

        roster_by_id = {
            p.player_id: p
            for p in roster_results
        }


        results = []


        for player_id, starter in starter_by_id.items():

            roster = roster_by_id.get(player_id)

            if roster is None:
                continue


            results.append(
                PlayerWAR(
                    player_id=starter.player_id,

                    name=starter.name,
                    position=starter.position,
                    team=starter.team,
                    age=starter.age,

                    projection=starter.projection,

                    starter_replacement=starter.replacement,
                    roster_replacement=roster.replacement,

                    war=roster.war,
                    war_per_game=roster.war_per_game,

                    starter_war=starter.war,
                    roster_war=roster.war,

                    starter_war_per_game=starter.war_per_game,
                    roster_war_per_game=roster.war_per_game,

                    model_version=starter.model_version,
                )
            )


        logger.info(
            f"Merged {len(results)} WAR results"
        )


        return sorted(
            results,
            key=lambda x: x.roster_war,
            reverse=True,
        )