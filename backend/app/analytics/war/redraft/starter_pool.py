from .positions import PositionRules

class StarterPoolCalculator:

    def select(
        self,
        players,
        roster_positions,
        teams,
    ):

        native, flex, superflex = PositionRules.demand(
            roster_positions,
            teams,
        )

        used = set()
        starters = []

        def consume(pool, amount):
            selected = []

            for player in sorted(
                [p for p in pool if p.projected_points > 0],
                key=lambda x: x.projected_points,
                reverse=True,
            ):

                if len(selected) >= amount:
                    break

                if player.player_id in used:
                    continue

                used.add(player.player_id)
                selected.append(player)

            return selected


        for position, amount in native.items():

            starters.extend(
                consume(
                    [
                        p for p in players
                        if p.position == position
                    ],
                    amount,
                )
            )


        starters.extend(
            consume(
                [
                    p for p in players
                    if p.position in PositionRules.eligible("FLEX")
                ],
                flex,
            )
        )


        starters.extend(
            consume(
                [
                    p for p in players
                    if p.position in PositionRules.eligible("SUPER_FLEX")
                ],
                superflex,
            )
        )


        return starters