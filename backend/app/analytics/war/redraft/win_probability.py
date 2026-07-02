import math


class WinProbabilityCalculator:

    def calculate(
        self,
        player_points,
        replacement_points,
        environment,
    ):

        weekly_upgrade = (
            player_points -
            replacement_points
        ) / environment.weeks


        player_team_score = (
            environment.average_team_ppg
            +
            weekly_upgrade
        )


        replacement_team_score = (
            environment.average_team_ppg
        )


        player_win_rate = self.probability(
            player_team_score,
            replacement_team_score,
            environment.scoring_std_dev,
        )


        replacement_win_rate = self.probability(
            replacement_team_score,
            replacement_team_score,
            environment.scoring_std_dev,
        )


        return (
            player_win_rate -
            replacement_win_rate
        ) * environment.weeks



    def probability(
        self,
        team_score,
        opponent_score,
        std_dev,
    ):

        if std_dev == 0:
            return .5


        difference = (
            team_score -
            opponent_score
        )


        z = difference / std_dev


        return (
            0.5 *
            (
                1 +
                math.erf(
                    z / math.sqrt(2)
                )
            )
        )

    def calculate_roster_war(
        self,
        starters: list,
        bench_players: list,
        starter_replacement: dict[str, float],
        bench_replacement: dict[str, float],
        environment,
    ) -> float:
        """
        Roster WAR = sum of starter contributions (can be negative if forced to start a bad player)
                + sum of bench contributions (floored at 0 — holding a bad player doesn't cost wins)
        """
        total = 0.0

        for player in starters:
            repl = starter_replacement.get(player.position)
            if repl is None:
                continue
            # Starters CAN be negative — if you're forced to start a bad player that hurts you
            total += self.calculate(player.projected_points, repl, environment)

        for player in bench_players:
            repl = bench_replacement.get(player.position, 0)
            # Bench players floor at 0 — you'd just cut them if they were truly worthless
            bench_war = self.calculate(player.projected_points, repl, environment)
            total += max(0.0, bench_war)

        return total