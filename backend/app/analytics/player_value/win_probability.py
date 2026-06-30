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