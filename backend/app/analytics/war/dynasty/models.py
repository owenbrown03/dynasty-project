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
    starter_war: float
    roster_war: float


class DynastyProjection(BaseModel):
    player_id: str
    name: str
    position: str
    team: str | None = None
    age: float

    current_starter_war: float
    current_roster_war: float
    future_starter_war: float
    future_roster_war: float
    total_starter_war: float
    total_roster_war: float
    total_starter_multiplier: float | None = None
    total_roster_multiplier: float | None = None

    expected_games_remaining: float
    seasons_remaining: float

    career_multiplier: float | None = None
    