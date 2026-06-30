from sqlmodel import BigInteger, SQLModel, Field, Column, Relationship
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import String, JSON, UniqueConstraint, Index
from typing import List, Dict, Optional, Any

from app.analytics.player_value.constants import FANTASY_GAMES_PER_SEASON

class InternalState(SQLModel, table=True):
    key: str = Field(primary_key=True)
    value: str

class League(SQLModel, table=True):
    league_id: str = Field(primary_key=True)
    name: str
    total_rosters: int
    draft_id: str = Field(unique=True, index=True)
    avatar: Optional[str] = Field(default=None, nullable=True)
    season: str
    dynasty: bool
    settings: dict[str, float] = Field(default_factory=dict, sa_type=JSON)
    scoring_settings: dict[str, float] = Field(default_factory=dict, sa_type=JSON)
    roster_positions: list[str] = Field(sa_column=Column(ARRAY(String)))

    roster: List["Roster"] = Relationship(back_populates="league", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    transaction: List["Transaction"] = Relationship(back_populates="league")
    draft: List["Draft"] = Relationship(back_populates="league")

    
class Roster(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    roster_id: Optional[int] = Field(default=None, index=True, nullable=True)
    owner_id: Optional[str] = Field(default=None, foreign_key="user.user_id", index=True)
    league_id: str = Field(foreign_key="league.league_id", index=True)
    
    players: Optional[List[str]] = Field(default=None, sa_column=Column(ARRAY(String)))
    
    fpts: int = Field(default=0)
    fpts_against: int = Field(default=0)
    wins: int = Field(default=0)
    ties: int = Field(default=0)
    losses: int = Field(default=0)

    league: "League" = Relationship(back_populates="roster")
    user: Optional["User"] = Relationship(back_populates="roster")

    __table_args__ = (
        UniqueConstraint("league_id", "roster_id", name="uq_roster_league_roster_id"),
        Index("idx_roster_owner_league", "owner_id", "league_id"),
        {"sqlite_autoincrement": True},
    )

class User(SQLModel, table=True):
    user_id: str = Field(primary_key=True)
    display_name: str
    avatar: Optional[str] = Field(default=None, nullable=True)
    is_owner: Optional[bool] = Field(default=None, nullable=True)
    is_placeholder: bool = Field(default=False, nullable=False)

    roster: List["Roster"] = Relationship(back_populates="user")

class Transaction(SQLModel, table=True):
    transaction_id: str = Field(primary_key=True)
    type: str = Field(index=True)
    time_ms: int = Field(sa_column=Column(BigInteger, nullable=False))
    league_id: str = Field(foreign_key="league.league_id", index=True)

    league: "League" = Relationship(back_populates="transaction")
    movement: List["Movement"] = Relationship(back_populates="transaction")
    draft_pick: List["TradedPick"] = Relationship(back_populates="transaction")
    waiver_budget: List["WaiverBudget"] = Relationship(back_populates="transaction")

class Draft(SQLModel, table=True):
    draft_id: str = Field(primary_key=True)
    league_id: str = Field(foreign_key="league.league_id", index=True)
    season: str = Field(index=True)
    draft_order: Optional[Dict[str, int]] = Field(default_factory=dict, sa_type=JSON, nullable=True)
    slot_to_roster_id: Optional[Dict[str, int]] = Field(default_factory=dict, sa_type=JSON, nullable=True)

    league: "League" = Relationship(back_populates="draft")

class Movement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    transaction_id: str = Field(foreign_key="transaction.transaction_id", index=True)
    player_id: Optional[str] = Field(default=None, index=True, nullable=True)
    roster_id: Optional[int] = Field(default=None, index=True, nullable=True)
    action: Optional[str] = Field(default=None, index=True, nullable=True)

    transaction: "Transaction" = Relationship(back_populates="movement")

    __table_args__ = (
        Index("idx_movement_roster_tx", "roster_id", "transaction_id"),
    )

class WaiverBudget(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    transaction_id: str = Field(foreign_key="transaction.transaction_id", index=True)
    sender: int = Field(index=True)
    receiver: int = Field(index=True)
    amount: int

    transaction: "Transaction" = Relationship(back_populates="waiver_budget")

class TradedPick(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    transaction_id: str = Field(foreign_key="transaction.transaction_id", index=True)
    season: str = Field(index=True)
    round: int = Field(index=True)
    new_roster_id: int = Field(index=True)
    old_roster_id: int = Field(index=True)
    og_roster_id: int = Field(index=True)

    transaction: "Transaction" = Relationship(back_populates="draft_pick")

class Player(SQLModel, table=True):
    player_id: str = Field(primary_key=True)
    position: Optional[str] = Field(default=None, nullable=True, index=True)
    team: Optional[str] = Field(default=None, nullable=True, index=True)
    first_name: str = Field(index=True)
    last_name: str = Field(index=True)
    years_exp: Optional[int] = Field(default=None, nullable=True, index=True)
    birth_date: Optional[str] = Field(default=None, nullable=True, index=True)

    projections: list["PlayerProjection"] = Relationship(back_populates="player")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
class PlayerProjection(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: str = Field(foreign_key="player.player_id", index=True)
    season: int = Field(index=True)
    source: str = Field(default="sleeper", index=True)
    projected_points: float = 0
    projected_ppg: float = 0
    games_played: float = FANTASY_GAMES_PER_SEASON

    # Passing
    pass_att: float = 0
    pass_cmp: float = 0
    pass_yd: float = 0
    pass_td: float = 0
    pass_int: float = 0
    pass_2pt: float = 0

    # Rushing
    rush_att: float = 0
    rush_yd: float = 0
    rush_td: float = 0
    rush_2pt: float = 0

    # Receiving
    rec: float = 0
    rec_yd: float = 0
    rec_td: float = 0
    rec_2pt: float = 0

    # Misc
    fum_lost: float = 0

    # First downs
    pass_fd: float = 0
    rush_fd: float = 0
    rec_fd: float = 0

    # Big play bonuses
    rec_0_4: float = 0
    rec_5_9: float = 0
    rec_10_19: float = 0
    rec_20_29: float = 0
    rec_30_39: float = 0
    rec_40p: float = 0

    bonus_rec_rb: float = 0
    bonus_rec_wr: float = 0
    bonus_rec_te: float = 0

    player: Optional["Player"] = Relationship(back_populates="projections")

    def to_stats(self) -> dict[str, Any]:
        excluded = {
            "id",
            "player_id",
            "season",
            "source",
            "projected_points",
            "projected_ppg",
            "games_played",
        }

        return {
            key: value
            for key, value in self.model_dump().items()
            if key not in excluded
        }