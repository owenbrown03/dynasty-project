class RosterValueCalculator:

    def calculate_floors(
        self,
        players,
        roster_distribution,
    ):

        floors = {}

        for position, count in roster_distribution.items():

            position_players = sorted(
                (
                    p
                    for p in players
                    if p.position == position
                ),
                key=lambda p: p.projected_points,
                reverse=True,
            )

            if not position_players:
                floors[position] = 0
                continue

            index = min(
                count - 1,
                len(position_players) - 1,
            )

            floors[position] = (
                position_players[index]
                .projected_points
            )

        return floors

    def calculate(
        self,
        projected_points,
        floor_points,
    ):

        return max(
            0.0,
            projected_points - floor_points,
        )