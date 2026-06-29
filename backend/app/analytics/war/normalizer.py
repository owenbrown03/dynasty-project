import logging

from app.analytics.war.models import PlayerProjectionValue
from app.integrations.sleeper.schemas.api import (
    Projection,
    Player,
)


logger = logging.getLogger(__name__)


FANTASY_POSITIONS = {
    "QB",
    "RB",
    "WR",
    "TE",
}


class ProjectionNormalizer:


    async def normalize(
        self,
        projections: list[Projection],
        players: dict[str, Player],
    ) -> list[PlayerProjectionValue]:


        result = []

        skipped_zero = 0
        skipped_position = 0
        missing_player = 0


        for projection in projections:

            if projection.pts_ppr <= 0:
                skipped_zero += 1
                continue


            player = players.get(
                projection.player_id
            )


            if not player:
                missing_player += 1
                continue


            if player.position not in FANTASY_POSITIONS:
                skipped_position += 1
                continue


            result.append(
                PlayerProjectionValue(
                    player_id=projection.player_id,
                    name=player.full_name,
                    position=player.position,
                    team=player.team,
                    projected_points=float(
                        projection.pts_ppr
                    ),
                    projected_ppg=(
                        float(projection.pts_ppr) / 17
                    ),
                )
            )


        logger.info(
            f"""
            Projection normalization complete

            normalized:
                {len(result)}

            skipped zero:
                {skipped_zero}

            skipped position:
                {skipped_position}

            missing player:
                {missing_player}
            """
        )


        return result