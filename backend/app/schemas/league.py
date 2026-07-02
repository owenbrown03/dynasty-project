from typing import Optional
from pydantic import BaseModel

from app.schemas.player import PlayerValue


class RosterSummary(BaseModel):
    ktc_total: int
    fantasycalc_total: int
    war_total: float
    average_age: Optional[float]
    player_count: int


class RosterManifest(BaseModel):
    roster_id: int
    owner_id: Optional[str]

    summary: RosterSummary

    players: list[PlayerValue]


class LeagueManifest(BaseModel):
    league_id: str
    league_name: str
    rosters: list[RosterManifest]