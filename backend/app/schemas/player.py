from pydantic import BaseModel


class PlayerValue(BaseModel):
    player_id: str

    name: str
    position: str | None
    team: str | None
    age: float | None = None

    ktc_value: int | None = None
    fc_value: int | None = None
    underdog_position_rank: str | None = None

    starter_war: float | None = None
    roster_war: float | None = None