from pydantic import Field, field_validator
from typing import List, Dict, Optional, Any

from app.schemas.base import Base
from app.analytics.war.redraft.constants import FANTASY_GAMES_PER_SEASON

class User(Base):
    user_id: str
    display_name: str
    avatar: Optional[str] = None
    is_owner: Optional[bool] = None

class LeagueSettings(Base):
    model_config = {"extra": "allow"}
    best_ball: int = 0
    waiver_budget: int = 100
    reserve_slots: int = 0
    taxi_slots: int = 0
    draft_rounds: int = 4
    playoff_teams: int = 6
    trade_deadline: Optional[int] = None
    num_teams: int = 12
    type: int = 0

class ScoringSettings(Base):
    model_config = {"extra": "allow"}
    pass_yd: float = 0.0
    pass_td: float = 0.0
    pass_int: float = 0.0
    rush_yd: float = 0.0
    rush_td: float = 0.0
    rec: float = 0.0
    rec_yd: float = 0.0
    rec_td: float = 0.0
    fum_lost: float = 0.0
    bonus_rec_te: float = 0.0

class League(Base):
    league_id: str
    name: str
    avatar: Optional[str] = None
    season: str
    status: str = "pre_draft"
    total_rosters: int
    draft_id: str
    previous_league_id: Optional[str] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)

    settings: LeagueSettings = Field(default_factory=LeagueSettings)

    scoring_settings: ScoringSettings = Field(
        default_factory=ScoringSettings
    )

    roster_positions: List[str] = Field(default_factory=list)

    @field_validator("metadata", mode="before")
    @classmethod
    def normalize_metadata(cls, value):
        return value or {}

    @field_validator("settings", mode="before")
    @classmethod
    def normalize_settings(cls, value):
        return value or {}

    @field_validator("scoring_settings", mode="before")
    @classmethod
    def normalize_scoring_settings(cls, value):
        return value or {}

    @field_validator("roster_positions", mode="before")
    @classmethod
    def normalize_roster_positions(cls, value):
        return value or []

class RosterSettings(Base):
    model_config = {"extra": "allow"}
    fpts: float = 0
    fpts_decimal: float = 0
    wins: int = 0
    losses: int = 0
    ties: int = 0
    total_moves: int = 0
    waiver_budget_used: int = 0
    waiver_position: int = 0

class Roster(Base):
    roster_id: int
    owner_id: Optional[str] = None
    league_id: str

    players: List[str] = Field(default_factory=list)
    starters: List[str] = Field(default_factory=list)
    reserve: List[str] = Field(default_factory=list)
    taxi: List[str] = Field(default_factory=list)

    metadata: Dict[str, Any] = Field(default_factory=dict)

    settings: RosterSettings = Field(
        default_factory=RosterSettings
    )

    @field_validator(
        "players",
        "starters",
        "reserve",
        "taxi",
        mode="before",
    )
    @classmethod
    def normalize_player_lists(cls, value):
        return value or []

    @field_validator("metadata", mode="before")
    @classmethod
    def normalize_metadata(cls, value):
        return value or {}

    @field_validator("settings", mode="before")
    @classmethod
    def normalize_settings(cls, value):
        return value or {}

class BracketSource(Base):
    w: Optional[int] = None 
    l: Optional[int] = None 

class Matchup(Base):
    r: int = Field(..., alias="r")
    m: int = Field(..., alias="m")
    t1: Optional[int] = None
    t2: Optional[int] = None
    t1_from: Optional[BracketSource] = None
    t2_from: Optional[BracketSource] = None
    w: Optional[int] = None
    l: Optional[int] = None
    p: Optional[int] = None

class WaiverBudget(Base):
    sender: int
    receiver: int
    amount: int  

class TradedPicks(Base):
    season: str
    round: int
    roster_id: int
    previous_owner_id: int
    owner_id: int

class Transaction(Base):
    transaction_id: str
    status_updated: int
    type: str
    roster_ids: List[int] = []
    adds: Optional[Dict[str, int]] = None
    drops: Optional[Dict[str, int]] = None
    waiver_budget: List[WaiverBudget] = []
    draft_picks: List[TradedPicks] = []

class Draft(Base):
    draft_id: str
    league_id: str
    season: str
    draft_order: Optional[Dict[str, int]] = {}
    slot_to_roster_id: Optional[Dict[str, int]] = {}

class Player(Base):
    player_id: str
    position: Optional[str] = None
    team: Optional[str] = None
    first_name: str
    last_name: str
    years_exp: Optional[int] = None
    birth_date: Optional[str] = None
    status: Optional[str] = None
    injury_status: Optional[str] = None
    injury_body_part: Optional[str] = None
    active: bool = True

type PlayerMap = Dict[str, Player]

class PlayerSummary(Base):
    player_id: str
    first_name: str
    last_name: str
    position: Optional[str] = None
    team: Optional[str] = None
    age: Optional[int] = None
    war: Optional[float] = None
    dynasty_war: Optional[float] = None
    fantasycalc_value: Optional[int] = None
    ktc_value: Optional[int] = None

class TrendingPlayer(Base):
    player_id: str
    count: int

class NFLState(Base):
    season: str
    week: int

class ProjectionStats(Base):
    gp: float = FANTASY_GAMES_PER_SEASON

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

    # Optional bonus stats
    rec_fd: float = 0
    rush_fd: float = 0
    pass_fd: float = 0

    rec_40p: float = 0
    rec_30_39: float = 0
    rec_20_29: float = 0
    rec_10_19: float = 0
    rec_5_9: float = 0
    rec_0_4: float = 0

    bonus_rec_rb: float = 0
    bonus_rec_wr: float = 0
    bonus_rec_te: float = 0
    
class Projection(Base):
    player_id: str
    stats: ProjectionStats