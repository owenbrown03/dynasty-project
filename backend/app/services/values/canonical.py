from types import SimpleNamespace


CANONICAL_WAR_ROSTER_POSITIONS = [
    "QB",
    "RB",
    "RB",
    "WR",
    "WR",
    "TE",
    "FLEX",
    "FLEX",
    "SUPER_FLEX",
    "BN",
    "BN",
    "BN",
    "BN",
    "BN",
    "BN",
]

CANONICAL_WAR_SCORING = {
    "pass_yd": 0.04,
    "pass_td": 4.0,
    "pass_int": -2.0,
    "rush_yd": 0.1,
    "rush_td": 6.0,
    "rec": 1.0,
    "rec_yd": 0.1,
    "rec_td": 6.0,
    "fum_lost": -2.0,
}


def build_canonical_war_league(
    season: int,
) -> SimpleNamespace:
    return SimpleNamespace(
        season=season,
        total_rosters=12,
        scoring_settings=CANONICAL_WAR_SCORING,
        roster_positions=CANONICAL_WAR_ROSTER_POSITIONS,
    )
