from collections import defaultdict

from .models import PlayerProjectionValue
from .positions import PositionRules

import logging
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
    
class ReplacementRosterBuilder:

    def build(
        self,
        players,
        roster_positions,
        total_rosters,
    ):

        native = defaultdict(int)

        flex = 0
        superflex = 0

        bench = (
            roster_positions.count("BN")
            * total_rosters
        )

        for slot in roster_positions:

            if slot == "BN":
                continue

            if slot == "FLEX":
                flex += total_rosters

            elif slot == "SUPER_FLEX":
                superflex += total_rosters

            else:
                native[slot] += total_rosters

        pools = defaultdict(list)

        for player in players:

            pools[player.position].append(player)

        for position in pools:

            pools[position].sort(
                key=lambda x: x.projected_points,
                reverse=True,
            )

        rostered = []

        used = set()

        def consume(pool, amount):

            count = 0

            for player in pool:

                if player.player_id in used:
                    continue

                used.add(player.player_id)
                rostered.append(player)

                count += 1

                if count >= amount:
                    break

        # Native starters

        for position, amount in native.items():

            consume(
                pools[position],
                amount,
            )

        # FLEX

        flex_pool = []

        for pos in PositionRules.eligible("FLEX"):

            flex_pool.extend(
                [
                    p
                    for p in pools[pos]
                    if p.player_id not in used
                ]
            )

        flex_pool.sort(
            key=lambda x: x.projected_points,
            reverse=True,
        )

        consume(
            flex_pool,
            flex,
        )

        # SUPER FLEX

        sf_pool = []

        for pos in PositionRules.eligible("SUPER_FLEX"):

            sf_pool.extend(
                [
                    p
                    for p in pools[pos]
                    if p.player_id not in used
                ]
            )

        sf_pool.sort(
            key=lambda x: x.projected_points,
            reverse=True,
        )

        consume(
            sf_pool,
            superflex,
        )

        # Bench

        remaining = sorted(
            [
                p
                for p in players
                if p.player_id not in used
            ],
            key=lambda x: x.projected_points,
            reverse=True,
        )

        rostered.extend(
            remaining[:bench]
        )

        return rostered


class BenchReplacementCalculator:

    def calculate(
        self,
        players,
        replacement_roster,
    ):

        rostered_ids = {
            p.player_id
            for p in replacement_roster
        }

        waivers = [
            p
            for p in players
            if p.player_id not in rostered_ids
        ]

        pools = defaultdict(list)

        for player in waivers:

            pools[player.position].append(player)

        values = {}

        for position, pool in pools.items():

            pool.sort(
                key=lambda x: x.projected_points,
                reverse=True,
            )

            if pool:

                values[position] = (
                    pool[0].projected_points
                )

            else:

                values[position] = 0

        return values