from typing import Any


class FantasyScoringCalculator:
    """
    Converts raw Sleeper projected stats into fantasy points using
    a league's scoring settings.

    The calculator intentionally contains no football-specific logic.
    Every stat is driven entirely by the scoring settings.

    Example:

    stats = {
        "pass_yd": 350,
        "pass_td": 3,
        "pass_int": 1,
    }

    scoring = {
        "pass_yd": 0.04,
        "pass_td": 4,
        "pass_int": -2,
    }

    points =
        350 * .04 +
        3 * 4 +
        1 * -2
    """

    def calculate(
        self,
        stats: dict[str, Any] | None,
        scoring_settings: dict[str, float],
    ) -> float:

        if not stats:
            return 0.0

        total = 0.0

        for stat_name, value in stats.items():

            if value is None:
                continue

            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                continue

            multiplier = scoring_settings.get(stat_name)

            if multiplier is None:
                continue

            total += numeric_value * float(multiplier)

        return round(total, 4)
    
def parse_scoring_settings(
    scoring_settings: dict[str, Any] | None,
) -> dict[str, float]:
    """
    Converts Sleeper scoring settings into floats.

    Sleeper returns values like:

    {
        "pass_td": "4",
        "pass_yd": "0.04",
        "rec": "1",
        "fum_lost": "-2"
    }
    """

    if not scoring_settings:
        return {}

    parsed = {}

    for stat, value in scoring_settings.items():

        try:
            parsed[stat] = float(value)
        except (TypeError, ValueError):
            continue

    return parsed