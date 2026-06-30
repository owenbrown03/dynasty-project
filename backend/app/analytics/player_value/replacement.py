import logging
from collections import defaultdict

from app.analytics.player_value.models import PlayerProjectionValue
from app.analytics.player_value.positions import PositionRules

logger = logging.getLogger(__name__)


class ReplacementCalculator:

    def calculate(
        self,
        players: list[PlayerProjectionValue],
        roster_positions: list[str],
        total_rosters: int,
    ) -> dict[str, float]:

        logger.info(
            "Calculating replacement levels"
        )

        native_demand = defaultdict(int)

        flex_demand = 0
        superflex_demand = 0

        for slot in roster_positions:

            if slot == "BN":
                continue

            if slot == "FLEX":

                flex_demand += total_rosters

            elif slot == "SUPER_FLEX":

                superflex_demand += total_rosters

            else:

                native_demand[slot] += total_rosters

        logger.info(
            f"""
            Native demand:
            {dict(native_demand)}

            FLEX demand:
            {flex_demand}

            SUPER FLEX demand:
            {superflex_demand}
            """
        )

        # -----------------------------------------
        # Group players
        # -----------------------------------------

        pools = defaultdict(list)

        for player in players:

            if player.projected_points <= 0:
                continue

            pools[player.position].append(player)

        for position in pools:

            pools[position].sort(
                key=lambda x: x.projected_points,
                reverse=True,
            )

        consumed_ids = set()
        consumed_counts = defaultdict(int)

        def consume(player):

            consumed_ids.add(
                player.player_id
            )

            consumed_counts[
                player.position
            ] += 1

        # -----------------------------------------
        # Native starters
        # -----------------------------------------

        for position, amount in native_demand.items():

            for player in pools.get(position, [])[:amount]:

                consume(player)

        # -----------------------------------------
        # FLEX
        # -----------------------------------------

        flex_pool = []

        for position in PositionRules.eligible(
            "FLEX"
        ):

            for player in pools.get(position, []):

                if player.player_id not in consumed_ids:

                    flex_pool.append(player)

        flex_pool.sort(
            key=lambda x: x.projected_points,
            reverse=True,
        )

        for player in flex_pool[:flex_demand]:

            consume(player)

        # -----------------------------------------
        # SUPER FLEX
        # -----------------------------------------

        superflex_pool = []

        for position in PositionRules.eligible(
            "SUPER_FLEX"
        ):

            for player in pools.get(position, []):

                if player.player_id not in consumed_ids:

                    superflex_pool.append(player)

        superflex_pool.sort(
            key=lambda x: x.projected_points,
            reverse=True,
        )

        for player in superflex_pool[:superflex_demand]:

            consume(player)

        logger.info(
            f"""
            Consumed demand:

            {dict(consumed_counts)}
            """
        )

        # -----------------------------------------
        # Replacement Points
        # -----------------------------------------

        replacement = {}

        relevant_positions = (
            set(native_demand.keys())
            |
            PositionRules.eligible("SUPER_FLEX")
        )

        for position in relevant_positions:

            pool = pools.get(
                position,
                []
            )

            index = consumed_counts[position]

            if len(pool) > index:

                replacement[position] = (
                    pool[index]
                    .projected_points
                )

            else:

                replacement[position] = 0

        logger.info(
            f"""
            Replacement Points:

            {replacement}
            """
        )

        return replacement