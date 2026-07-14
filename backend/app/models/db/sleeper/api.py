from datetime import datetime

from sqlmodel import BigInteger, SQLModel, Column, Field, Relationship
from sqlalchemy import String, JSON, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import ARRAY
from typing import List, Dict, Optional, Any
from pydantic import field_validator

from ..underdog.models import UnderdogPlayerMap
from ..ktc.models import KTCPlayerMap
from ..fc.models import FantasyCalcValue
from app.analytics.war.redraft.constants import FANTASY_GAMES_PER_SEASON


class InternalState(SQLModel, table=True):
    key: str = Field(primary_key=True)
    value: str


class League(SQLModel, table=True):
    league_id: str = Field(primary_key=True)
    
    name: str
    avatar: Optional[str] = Field(default=None, nullable=True)
    season: str
    status: str = Field(default="pre_draft", index=True)
    total_rosters: int
    draft_id: str = Field(unique=True, index=True)
    
    previous_league_id: Optional[str] = Field(
        default=None,
        nullable=True,
        index=True,
    )

    league_metadata: dict = Field(
        default_factory=dict, 
        sa_type=JSON
    )

    settings: dict[str, Any] = Field(
        default_factory=dict,
        sa_type=JSON,
    )

    scoring_settings: dict[str, float] = Field(
        default_factory=dict,
        sa_type=JSON,
    )

    roster_positions: list[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String)),
    )
    
    @property
    def roster_size(self) -> int:
        return len(self.roster_positions)

    @property
    def starter_slots(self) -> int:
        return sum(
            pos not in {"BN", "IR", "TAXI"}
            for pos in self.roster_positions
        )

    @property
    def bench_slots(self) -> int:
        return self.roster_positions.count("BN")

    @property
    def taxi_slots(self) -> int:
        return self.settings.get("taxi_slots", 0)

    @property
    def reserve_slots(self) -> int:
        return self.settings.get("reserve_slots", 0)

    @property
    def waiver_budget(self) -> int:
        return self.settings.get("waiver_budget", 100)

    @property
    def playoff_teams(self) -> int:
        return self.settings.get("playoff_teams", 6)

    @property
    def trade_deadline(self):
        return self.settings.get("trade_deadline")

    @property
    def is_dynasty(self) -> bool:
        return self.settings.get("type", 0) == 2

    roster: List["Roster"] = Relationship(
        back_populates="league",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    transaction: List["Transaction"] = Relationship(back_populates="league")
    draft: List["Draft"] = Relationship(back_populates="league")
    sync_state: Optional["LeagueSyncState"] = Relationship(back_populates="league")


class LeagueSyncState(SQLModel, table=True):
    league_id: str = Field(primary_key=True, foreign_key="league.league_id")
    last_synced_week: int = Field(default=0)
    last_synced_at: datetime = Field(default_factory=datetime.now)
    last_full_synced_at: Optional[datetime] = Field(
        default=None,
        nullable=True,
    )

    league: Optional["League"] = Relationship(back_populates="sync_state")


class Roster(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    roster_id: int = Field(index=True)

    owner_id: Optional[str] = Field(
        default=None,
        foreign_key="user.user_id",
        index=True,
    )

    league_id: str = Field(
        foreign_key="league.league_id",
        index=True,
    )

    players: list[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String)),
    )

    starters: list[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String)),
    )

    reserve: list[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String)),
    )

    taxi: list[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String)),
    )

    roster_metadata: dict = Field(
        default_factory=dict, 
        sa_type=JSON
    )

    settings: dict[str, Any] = Field(
        default_factory=dict,
        sa_type=JSON,
    )
    
    is_owner: Optional[bool] = Field(default=None, nullable=True)
    
    @property
    def wins(self) -> int:
        return self.settings.get("wins", 0)

    @property
    def losses(self) -> int:
        return self.settings.get("losses", 0)

    @property
    def ties(self) -> int:
        return self.settings.get("ties", 0)

    @property
    def fpts(self) -> float:
        return (
            self.settings.get("fpts", 0)
            + self.settings.get("fpts_decimal", 0) / 100
        )

    @property
    def ppts(self) -> float:
        return (
            self.settings.get("ppts", 0)
            + self.settings.get("ppts_decimal", 0) / 100
        )

    @property
    def waiver_budget_used(self) -> int:
        return self.settings.get("waiver_budget_used", 0)

    @property
    def waiver_position(self) -> int:
        return self.settings.get("waiver_position", 0)

    @property
    def total_moves(self) -> int:
        return self.settings.get("total_moves", 0)

    @property
    def roster_size(self) -> int:
        return len(self.players)

    def faab_remaining(self, league: "League") -> int:
        return max(
            league.waiver_budget - self.waiver_budget_used,
            0,
        )

    def open_roster_spots(self, league: "League") -> int:
        max_players = (
            league.roster_size
            + league.taxi_slots
            + league.reserve_slots
        )

        return max_players - len(self.players)

    league: "League" = Relationship(back_populates="roster")
    user: Optional["User"] = Relationship(back_populates="roster")

    __table_args__ = (
        UniqueConstraint(
            "league_id",
            "roster_id",
            name="uq_roster_league_roster_id",
        ),
        Index(
            "idx_roster_owner_league",
            "owner_id",
            "league_id",
        ),
        {"sqlite_autoincrement": True},
    )


class User(SQLModel, table=True):
    user_id: str = Field(primary_key=True)
    display_name: str
    avatar: Optional[str] = Field(default=None, nullable=True)
    is_placeholder: bool = Field(default=False, nullable=False)

    roster: List["Roster"] = Relationship(back_populates="user")


class Transaction(SQLModel, table=True):
    transaction_id: str = Field(primary_key=True)
    type: str = Field(index=True)
    status: str | None = Field(
        default=None,
        index=True,
        nullable=True,
    )
    time_ms: int = Field(
        sa_column=Column(
            BigInteger,
            nullable=False,
        )
    )
    league_id: str = Field(
        foreign_key="league.league_id",
        index=True,
    )

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


class PlayoffMatchup(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    league_id: str = Field(
        foreign_key="league.league_id",
        index=True,
    )
    bracket_type: str = Field(index=True)
    round: int = Field(index=True)
    matchup_id: int = Field(index=True)
    team_one_roster_id: Optional[int] = Field(
        default=None,
        nullable=True,
    )
    team_two_roster_id: Optional[int] = Field(
        default=None,
        nullable=True,
    )
    team_one_from_winner_matchup_id: Optional[int] = Field(
        default=None,
        nullable=True,
    )
    team_one_from_loser_matchup_id: Optional[int] = Field(
        default=None,
        nullable=True,
    )
    team_two_from_winner_matchup_id: Optional[int] = Field(
        default=None,
        nullable=True,
    )
    team_two_from_loser_matchup_id: Optional[int] = Field(
        default=None,
        nullable=True,
    )
    winner_roster_id: Optional[int] = Field(
        default=None,
        nullable=True,
        index=True,
    )
    loser_roster_id: Optional[int] = Field(
        default=None,
        nullable=True,
        index=True,
    )
    placement: Optional[int] = Field(
        default=None,
        nullable=True,
        index=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "league_id",
            "bracket_type",
            "round",
            "matchup_id",
            name="uq_playoffmatchup_league_bracket_round_matchup",
        ),
    )


class Player(SQLModel, table=True):
    player_id: str = Field(primary_key=True)

    position: Optional[str] = Field(
        default=None,
        nullable=True,
        index=True,
    )

    team: Optional[str] = Field(
        default=None,
        nullable=True,
        index=True,
    )

    first_name: str = Field(index=True)

    last_name: str = Field(index=True)

    years_exp: Optional[int] = Field(
        default=None,
        nullable=True,
        index=True,
    )

    birth_date: Optional[str] = Field(
        default=None,
        nullable=True,
        index=True,
    )

    status: Optional[str] = Field(
        default=None,
        nullable=True,
        index=True,
    )

    injury_status: Optional[str] = Field(
        default=None,
        nullable=True,
    )

    injury_body_part: Optional[str] = Field(
        default=None,
        nullable=True,
    )

    active: bool = Field(default=True)

    projections: list["PlayerProjection"] = Relationship(
        back_populates="player"
    )

    season_stats: list["PlayerSeasonStats"] = Relationship(
        back_populates="player"
    )

    underdog: "UnderdogPlayerMap" = Relationship(
        back_populates="player"
    )

    ktc: "KTCPlayerMap" = Relationship(
        back_populates="player"
    )

    fantasycalc: "FantasyCalcValue" = Relationship(
        back_populates="player"
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def search_name(self) -> str:
        return f"{self.first_name} {self.last_name}".lower()

    @property
    def age(self) -> Optional[int]:
        if not self.birth_date:
            return None

        try:
            from datetime import date

            birth = date.fromisoformat(self.birth_date)

            today = date.today()

            return (
                today.year
                - birth.year
                - (
                    (today.month, today.day)
                    < (birth.month, birth.day)
                )
            )
        except ValueError:
            return None


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


class PlayerSeasonStats(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: str = Field(foreign_key="player.player_id", index=True)
    season: int = Field(index=True)
    season_type: str = Field(default="regular", index=True)
    source: str = Field(default="sleeper", index=True)
    games_played: float = 0

    pass_att: float = 0
    pass_cmp: float = 0
    pass_yd: float = 0
    pass_td: float = 0
    pass_int: float = 0
    pass_2pt: float = 0

    rush_att: float = 0
    rush_yd: float = 0
    rush_td: float = 0
    rush_2pt: float = 0

    rec: float = 0
    rec_yd: float = 0
    rec_td: float = 0
    rec_2pt: float = 0

    fum_lost: float = 0

    pass_fd: float = 0
    rush_fd: float = 0
    rec_fd: float = 0

    rec_0_4: float = 0
    rec_5_9: float = 0
    rec_10_19: float = 0
    rec_20_29: float = 0
    rec_30_39: float = 0
    rec_40p: float = 0

    bonus_rec_rb: float = 0
    bonus_rec_wr: float = 0
    bonus_rec_te: float = 0

    player: Optional["Player"] = Relationship(back_populates="season_stats")

    def to_stats(self) -> dict[str, Any]:
        excluded = {
            "id",
            "player_id",
            "season",
            "season_type",
            "source",
            "games_played",
        }

        return {
            key: value
            for key, value in self.model_dump().items()
            if key not in excluded
        }
