from dataclasses import dataclass


@dataclass
class WARSettings:
    """
    League configuration used for replacement level.

    Default:
    12 team league
    1 QB
    2 RB
    3 WR
    1 TE
    """

    teams: int = 12

    starting_qb: int = 1
    starting_rb: int = 2
    starting_wr: int = 3
    starting_te: int = 1

    # future use for flex replacement model
    flex_rb_wr_te: int = 1


@dataclass
class PlayerProjectionValue:
    """
    Normalized player projection data.

    This is the bridge between:
        Sleeper projections
                |
                v
        WAR analytics
    """

    player_id: str

    name: str

    position: str

    team: str | None

    projected_points: float

    projected_ppg: float


@dataclass
class PlayerWAR:
    """
    Final WAR calculation output.
    """

    player_id: str

    name: str

    position: str

    team: str | None

    projected_points: float

    replacement_points: float

    war: float

    war_per_game: float