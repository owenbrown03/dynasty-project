import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from .constants import FANTASY_GAMES_PER_SEASON

from app.utils.age import calculate_age

from app.models.db.sleeper.api import (
    League,
    Player,
    PlayerProjection,
)

from app.analytics.player_value.models import (
    PlayerProjectionValue,
)

from app.analytics.player_value.scoring import (
    FantasyScoringCalculator,
    parse_scoring_settings,
)

from app.analytics.player_value.replacement import (
    ReplacementCalculator,
)

from app.analytics.player_value.calculator import (
    WARCalculator,
)

from app.analytics.player_value.environment import (
    LeagueEnvironmentCalculator,
)

from app.analytics.player_value.starter_pool import (
    StarterPoolCalculator,
)

from app.analytics.player_value.win_probability import (
    WinProbabilityCalculator,
)

logger = logging.getLogger(__name__)


class WARService:

    def __init__(self):

        self.scoring_calculator = (
            FantasyScoringCalculator()
        )

        self.replacement_calculator = (
            ReplacementCalculator()
        )

        starter_pool = StarterPoolCalculator()

        self.environment_calculator = (
            LeagueEnvironmentCalculator(
                starter_pool,
            )
        )

        win_calculator = WinProbabilityCalculator()

        self.war_calculator = (
            WARCalculator(
                win_calculator,
            )
        )

    async def calculate(
        self,
        db: AsyncSession,
        league_id: str,
    ):

        logger.info(
            f"Starting WAR calculation for league {league_id}"
        )

        league = await db.get(
            League,
            league_id,
        )

        if not league:

            raise ValueError(
                f"League {league_id} not found"
            )

        logger.info(
            f"""
            League Loaded

            name={league.name}
            season={league.season}
            teams={league.total_rosters}

            roster_positions:
            {league.roster_positions}
            """
        )

        # -----------------------------------------
        # Parse league scoring
        # -----------------------------------------

        league_scoring = league.scoring_settings

        logger.info(
            f"Loaded {len(league_scoring)} scoring settings"
        )

        # -----------------------------------------
        # Load projections
        # -----------------------------------------

        result = await db.execute(
            select(PlayerProjection).where(
                PlayerProjection.season
                == int(league.season)
            )
        )

        projections = result.scalars().all()

        logger.info(
            f"Loaded projections: {len(projections)}"
        )

        # -----------------------------------------
        # Load players
        # -----------------------------------------

        result = await db.execute(
            select(Player)
        )

        players = {
            player.player_id: player
            for player in result.scalars()
        }

        # -----------------------------------------
        # League valid positions
        # -----------------------------------------

        league_positions = {
            slot
            for slot in league.roster_positions
            if slot not in {
                "BN",
                "FLEX",
                "SUPER_FLEX",
            }
        }

        logger.info(
            f"League positions: {league_positions}"
        )

        # -----------------------------------------
        # Normalize
        # -----------------------------------------

        normalized = []

        missing_players = 0
        invalid_position = 0

        for projection in projections:

            player = players.get(
                projection.player_id
            )

            if not player:

                missing_players += 1
                continue

            if (
                not player.position
                or player.position not in league_positions
            ):

                invalid_position += 1
                continue

            age = calculate_age(player.birth_date)

            stats = projection.to_stats()

            games_played = int(
                projection.games_played
                or FANTASY_GAMES_PER_SEASON
            )

            projected_points = (
                self.scoring_calculator.calculate(
                    stats=stats,
                    scoring_settings=league_scoring,
                )
            )

            projected_ppg = (
                projected_points / games_played
                if games_played
                else 0
            )

            normalized.append(
                PlayerProjectionValue(
                    player_id=projection.player_id,
                    name=player.full_name,
                    position=player.position,
                    team=player.team,
                    age=age,
                    stats=stats,
                    games_played=games_played,
                    projected_points=projected_points,
                    projected_ppg=projected_ppg,
                )
            )

        logger.info(
            f"""
            Normalization complete

            normalized={len(normalized)}

            missing_players={missing_players}

            invalid_position={invalid_position}
            """
        )

        if normalized:

            avg_ppg = (
                sum(
                    p.projected_ppg
                    for p in normalized
                )
                / len(normalized)
            )

            logger.info(
                f"""
                Fantasy scoring complete

                Average player PPG:
                {avg_ppg:.2f}
                """
            )

        # -----------------------------------------
        # League scoring environment
        # -----------------------------------------

        environment = (
            self.environment_calculator.calculate(
                players=normalized,

                roster_positions=(
                    league.roster_positions
                ),

                teams=(
                    league.total_rosters
                ),
            )
        )

        # -----------------------------------------
        # Replacement
        # -----------------------------------------

        replacement_values = (
            self.replacement_calculator.calculate(
                players=normalized,

                roster_positions=(
                    league.roster_positions
                ),

                total_rosters=(
                    league.total_rosters
                ),
            )
        )

        logger.info(
            "Replacement values:"
        )

        for pos, value in replacement_values.items():

            logger.info(
                f"{pos}: {value:.2f}"
            )

        # -----------------------------------------
        # WAR
        # -----------------------------------------

        results = (
            self.war_calculator.calculate(
                players=normalized,

                replacement_values=(
                    replacement_values
                ),

                environment=(
                    environment
                ),
            )
        )

        logger.info(
            f"WAR calculated for {len(results)} players"
        )

        return results