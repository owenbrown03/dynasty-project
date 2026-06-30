from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint

if TYPE_CHECKING:
    from ..sleeper.api import Player

class KTCPlayerMap(SQLModel, table=True):
    """Maps KTC's player name (used as their de facto key) to our canonical Sleeper player_id."""

    ktc_name: str = Field(primary_key=True)
    player_id: str = Field(foreign_key="player.player_id", index=True)
    matched_via: str = Field(default="exact")
    confidence: Optional[float] = Field(default=None, nullable=True)

    player: "Player" = Relationship(back_populates="ktc")

class KTCValue(SQLModel, table=True):
    """KTC trade value snapshot for a player."""

    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: str = Field(foreign_key="player.player_id", index=True)

    value: int = 0
    position_rank: Optional[str] = Field(default=None, nullable=True)
    sf_value: Optional[int] = Field(default=None, nullable=True)
    sf_position_rank: Optional[str] = Field(default=None, nullable=True)
    redraft_value: Optional[int] = Field(default=None, nullable=True)
    redraft_position_rank: Optional[str] = Field(default=None, nullable=True)
    sf_redraft_value: Optional[int] = Field(default=None, nullable=True)
    sf_redraft_position_rank: Optional[str] = Field(default=None, nullable=True)

    __table_args__ = (
        UniqueConstraint("player_id", name="uq_ktc_value_player"),
    )