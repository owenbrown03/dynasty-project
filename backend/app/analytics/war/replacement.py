import logging
from collections import defaultdict

from app.analytics.war.models import PlayerProjectionValue

logger = logging.getLogger(__name__)


# Approximate fantasy roster availability
# This represents how many players at each position are "startable"
ROSTER_SLOTS = {
    "QB": 32,
    "RB": 60,
    "WR": 80,
    "TE": 32,
    "K": 32,
    "DEF": 32,
}


FANTASY_POSITIONS = set(
    ROSTER_SLOTS.keys()
)


class ReplacementCalculator:

    def calculate(
        self,
        players: list[PlayerProjectionValue],
    ) -> dict[str, float]:

        logger.info(
            "Calculating replacement values..."
        )

        grouped = defaultdict(list)

        for player in players:

            if player.position not in FANTASY_POSITIONS:
                continue

            if player.projected_points <= 0:
                continue

            grouped[player.position].append(
                player
            )


        replacements = {}


        for position, position_players in grouped.items():

            position_players.sort(
                key=lambda x: x.projected_points,
                reverse=True,
            )


            roster_size = ROSTER_SLOTS.get(
                position,
                0,
            )


            if len(position_players) <= roster_size:
                replacement = 0

            else:
                replacement_player = position_players[
                    roster_size - 1
                ]

                replacement = (
                    replacement_player.projected_points
                )


            replacements[position] = replacement


            logger.info(
                f"""
                Replacement calculation

                Position:
                    {position}

                Players:
                    {len(position_players)}

                Roster slots:
                    {roster_size}

                Replacement:
                    {replacement}

                Replacement player:
                    {
                        position_players[roster_size - 1].name
                        if len(position_players) > roster_size
                        else "none"
                    }
                """
            )


        return replacements