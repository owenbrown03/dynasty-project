import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.db.sleeper.api import (
    Player,
    PlayerProjection,
)

from app.analytics.war.models import (
    PlayerProjectionValue,
    WARSettings,
)

from app.analytics.war.replacement import (
    ReplacementCalculator,
)

from app.analytics.war.calculator import (
    WARCalculator,
)


logger = logging.getLogger(__name__)


class WARService:

    def __init__(self):

        settings = WARSettings()

        self.replacement_calculator = (
            ReplacementCalculator(
                settings
            )
        )

        self.war_calculator = WARCalculator()


    async def calculate(
        self,
        db: AsyncSession,
        season: int,
    ):

        logger.info(
            f"Starting WAR calculation for {season}"
        )


        # -----------------------------------------
        # Load projections
        # -----------------------------------------

        projection_result = await db.execute(
            select(PlayerProjection)
            .where(
                PlayerProjection.season == season
            )
        )

        projections = (
            projection_result
            .scalars()
            .all()
        )


        logger.info(
            f"Loaded projections: {len(projections)}"
        )


        if projections:

            logger.info(
                "Sample projections:"
            )

            for p in projections[:10]:
                logger.info(
                    f"""
                    player_id={p.player_id}
                    points={p.projected_points}
                    ppg={p.projected_ppg}
                    """
                )


        # -----------------------------------------
        # Load players
        # -----------------------------------------

        player_result = await db.execute(
            select(Player)
        )

        players = {
            p.player_id: p
            for p in player_result.scalars()
        }


        logger.info(
            f"Loaded players: {len(players)}"
        )


        # -----------------------------------------
        # Normalize
        # -----------------------------------------

        normalized = []

        missing_players = 0
        missing_position = 0


        for projection in projections:

            player = players.get(
                projection.player_id
            )


            if not player:
                missing_players += 1

                logger.debug(
                    f"Missing player "
                    f"{projection.player_id}"
                )

                continue


            if not player.position:

                missing_position += 1

                logger.debug(
                    f"Missing position "
                    f"{player.full_name}"
                )

                continue


            normalized.append(
                PlayerProjectionValue(
                    player_id=(
                        projection.player_id
                    ),

                    name=(
                        player.full_name
                    ),

                    position=(
                        player.position
                    ),

                    team=(
                        player.team
                    ),

                    projected_points=(
                        projection.projected_points
                    ),

                    projected_ppg=(
                        projection.projected_ppg
                    ),
                )
            )


        logger.info(
            f"""
            Normalization complete

            normalized={len(normalized)}
            missing_players={missing_players}
            missing_position={missing_position}
            """
        )


        if normalized:

            logger.info(
                "Sample normalized players:"
            )

            for p in normalized[:10]:

                logger.info(
                    f"""
                    {p.name}
                    position={p.position}
                    team={p.team}
                    points={p.projected_points}
                    """
                )


        # -----------------------------------------
        # Replacement values
        # -----------------------------------------

        replacement_values = (
            self.replacement_calculator.calculate(
                normalized
            )
        )


        logger.info(
            "Replacement values:"
        )


        for position, value in (
            replacement_values.items()
        ):

            logger.info(
                f"{position}: {value}"
            )


        # -----------------------------------------
        # WAR calculation
        # -----------------------------------------

        war_results = (
            self.war_calculator.calculate(
                normalized,
                replacement_values,
            )
        )


        logger.info(
            f"WAR calculated for "
            f"{len(war_results)} players"
        )


        logger.info(
            "Top 25 WAR players:"
        )


        for player in war_results[:25]:

            logger.info(
                f"""
                {player.name}
                {player.position}
                {player.team}

                Projection:
                    {player.projected_points}

                Replacement:
                    {player.replacement_points}

                WAR:
                    {player.war}
                """
            )


        return war_results