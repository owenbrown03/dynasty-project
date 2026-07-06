from typing import Optional

from app.schemas.base import Base
from app.schemas.player import PlayerValue


class RosterSummary(Base):
    ktc_total: int
    fantasycalc_total: int
    war_total: float
    average_age: Optional[float]
    player_count: int


class RosterManifest(Base):
    roster_id: int
    owner_id: Optional[str]

    summary: RosterSummary

    players: list[PlayerValue]


class LeagueManifest(Base):
    league_id: str
    league_name: str
    rosters: list[RosterManifest]