from app.schemas.base import Base


class PlayerValue(Base):
    player_id: str

    name: str
    position: str | None
    team: str | None
    age: float | None = None

    ktc_value: int | None = None
    fc_value: int | None = None
    underdog_position_rank: str | None = None

    redraft_starter_war: float | None = None
    redraft_roster_war: float | None = None

    dynasty_starter_war: float | None = None
    dynasty_roster_war: float | None = None
    my_redraft_starter_war: float | None = None
    my_redraft_roster_war: float | None = None
    my_dynasty_starter_war: float | None = None
    my_dynasty_roster_war: float | None = None

    dynasty_expected_games_remaining: float | None = None
    dynasty_seasons_remaining: float | None = None
