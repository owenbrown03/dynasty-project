from collections import defaultdict


class PositionRules:


    FLEX_ELIGIBLE = {
        "RB",
        "WR",
        "TE",
    }


    SUPERFLEX_ELIGIBLE = {
        "QB",
        "RB",
        "WR",
        "TE",
    }


    @classmethod
    def demand(
        cls,
        roster_positions: list[str],
        teams: int,
    ):

        native = defaultdict(int)

        flex = 0

        superflex = 0


        for slot in roster_positions:

            if slot == "BN":
                continue


            if slot == "FLEX":

                flex += teams


            elif slot == "SUPER_FLEX":

                superflex += teams


            else:

                native[slot] += teams


        return (
            dict(native),
            flex,
            superflex,
        )



    @classmethod
    def eligible(
        cls,
        slot: str,
    ):

        if slot == "FLEX":

            return cls.FLEX_ELIGIBLE


        if slot == "SUPER_FLEX":

            return cls.SUPERFLEX_ELIGIBLE


        return {
            slot
        }