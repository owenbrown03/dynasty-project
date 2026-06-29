from typing import Optional
from pydantic import BaseModel


class UnderdogTeam(BaseModel):
    id: str
    abbr: str
    name: str
    short_name: str
    sport_id: str


class UnderdogPlayer(BaseModel):
    id: str
    first_name: str
    last_name: str
    position_name: str
    position_display_name: str
    team_id: Optional[str]
    sport_id: str


class UnderdogProjection(BaseModel):
    id: int
    adp: Optional[float]
    avg_weekly_points: Optional[float]
    points: Optional[float]
    position_rank: Optional[str]      # e.g. "WR1", "RB3"
    salary: Optional[str]
    scoring_type_id: str


class UnderdogAppearance(BaseModel):
    id: str
    player_id: str
    team_id: Optional[str]
    match_id: int
    match_type: str
    position_id: str
    projection: Optional[UnderdogProjection]

    # Enriched after joining with players/teams — not in raw API
    player: Optional[UnderdogPlayer] = None
    team_abbr: Optional[str] = None


class UnderdogSlate(BaseModel):
    id: str
    title: str
    description: str
    sport_id: str
    best_ball: bool
    lobby_hidden: bool
    rank: int
    contest_style_ids: list[str]
    cutoff_at: Optional[str]
    start_at: Optional[str]


class UnderdogContestStyle(BaseModel):
    id: str
    name: str
    sport_id: str
    best_ball: bool
    status: str
    scoring_type_id: str
    rounds: int
