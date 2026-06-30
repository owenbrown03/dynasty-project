from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint, Index

if TYPE_CHECKING:
    from ..sleeper.api import Player

class UnderdogPlayerMap(SQLModel, table=True):
    """Maps Underdog's UUID player_id to our canonical Sleeper player_id."""

    underdog_id: str = Field(primary_key=True)
    player_id: str = Field(foreign_key="player.player_id", index=True)
    matched_via: str = Field(default="exact")  # "exact" | "fuzzy" | "override" | "manual"
    confidence: Optional[float] = Field(default=None, nullable=True)

    player: "Player" = Relationship(back_populates="underdog")

class UnderdogADP(SQLModel, table=True):
    """ADP snapshot for a player on a given slate/scoring format."""

    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: str = Field(foreign_key="player.player_id", index=True)
    slate_id: str = Field(index=True)
    scoring_type_id: str = Field(index=True)
    superflex: bool = Field(default=False, index=True)

    adp: float = 0
    position_rank: Optional[str] = Field(default=None, nullable=True)
    avg_weekly_points: Optional[float] = Field(default=None, nullable=True)
    salary: Optional[float] = Field(default=None, nullable=True)

    __table_args__ = (
        UniqueConstraint("player_id", "slate_id", "scoring_type_id", name="uq_underdog_adp_player_slate"),
        Index("idx_underdog_adp_superflex", "superflex"),
    )