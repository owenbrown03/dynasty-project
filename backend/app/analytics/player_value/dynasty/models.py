from pydantic import BaseModel


class ExpectedGamesRemaining(BaseModel):
    age: float
    position: str
    years_remaining: float
    games_remaining: float


class DynastyPlayerInput(BaseModel):
    player_id: str
    name: str
    position: str
    team: str | None = None
    age: float
    war: float


class DynastyProjection(BaseModel):
    player_id: str
    name: str
    position: str
    team: str | None = None

    current_war: float
    current_age: float

    future_war: float
    total_war: float

    expected_games_remaining: float
    seasons_remaining: float

    career_multiplier: float | None = None
    total_multiplier: float | None = None