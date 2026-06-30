from pydantic import BaseModel, Field

from .constants import FANTASY_GAMES_PER_SEASON


class PlayerProjectionValue(BaseModel):
    player_id: str
    name: str
    position: str
    age: float
    team: str | None = None
    stats: dict[str, float] = Field(default_factory=dict)
    games_played: int = FANTASY_GAMES_PER_SEASON
    projected_points: float
    projected_ppg: float


class LeagueEnvironment(BaseModel):
    teams: int
    starting_slots: int
    total_starter_slots: int
    average_team_points: float
    average_team_ppg: float
    scoring_std_dev: float
    weeks: int = FANTASY_GAMES_PER_SEASON
    replacement_points: dict[str,float]


class PlayerWAR(BaseModel):
    player_id: str
    name: str
    position: str
    team: str | None = None
    age: float
    projection: float
    replacement: float
    war: float
    war_per_game: float
    model_version: str