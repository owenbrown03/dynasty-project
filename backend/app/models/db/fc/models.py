from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint, Index

if TYPE_CHECKING:
    from ..sleeper.api import Player


class FantasyCalcValue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: str = Field(foreign_key="player.player_id", index=True)
    is_dynasty: bool = Field(default=True, index=True)
    num_qbs: int = Field(default=1, index=True)
    num_teams: int = Field(default=12, index=True)
    ppr: int = Field(default=1, index=True)
    value: int = 0
    overall_rank: Optional[int] = None
    position_rank: Optional[int] = None
    trend_30_day: Optional[int] = None
    redraft_value: Optional[int] = None
    combined_value: Optional[int] = None
    tier: Optional[int] = None
    adp: Optional[float] = None

    player: "Player" = Relationship(back_populates="fantasycalc")

    __table_args__ = (
        UniqueConstraint(
            "player_id",
            "is_dynasty",
            "num_qbs",
            "num_teams",
            "ppr",
            name="uq_fantasycalc_value_format",
        ),
        Index(
            "idx_fantasycalc_value_player",
            "player_id",
        ),
    )