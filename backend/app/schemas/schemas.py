from pydantic import BaseModel, ConfigDict, Field, computed_field
from typing import List, Dict, Optional

class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, 
        extra='ignore',
        frozen=True
    )

class SleeperUser(BaseSchema):
    user_id: str
    display_name: str
    avatar: Optional[str] = None
    is_owner: Optional[bool] = None

class LeagueSettings(BaseSchema):
    best_ball: Optional[bool] = False
    trade_deadline: Optional[int] = None
    type: int

class ScoringSettings(BaseSchema):
    bonus_rec_te: float = 0.0
    rec: float = 0.0
    pass_td: float = 0.0

class SleeperLeague(BaseSchema):
    league_id: str
    name: str
    total_rosters: int
    draft_id: str
    avatar: Optional[str] = None
    season: str    
    settings: Optional[LeagueSettings] = None
    scoring_settings: Optional[ScoringSettings] = None
    roster_positions: Optional[List[str]] = None

class RosterSettings(BaseSchema):
    fpts: Optional[int] = 0
    fpts_against: Optional[int] = 0
    wins: Optional[int] = 0
    ties: Optional[int] = 0
    losses: Optional[int] = 0

class SleeperRoster(BaseSchema):
    roster_id: int
    owner_id: Optional[str] = None 
    league_id: str
    players: Optional[List[str]] = None
    settings: RosterSettings

class BracketSource(BaseSchema):
    w: Optional[int] = None 
    l: Optional[int] = None 

class SleeperMatchup(BaseSchema):
    r: int = Field(..., alias="r")
    m: int = Field(..., alias="m")
    t1: Optional[int] = None
    t2: Optional[int] = None
    t1_from: Optional[BracketSource] = None
    t2_from: Optional[BracketSource] = None
    w: Optional[int] = None
    l: Optional[int] = None
    p: Optional[int] = None

class WaiverBudget(BaseSchema):
    sender: int
    receiver: int
    amount: int  

class TradedPicks(BaseSchema):
    season: str
    round: int
    roster_id: int
    previous_owner_id: int
    owner_id: int

class SleeperTransaction(BaseSchema):
    transaction_id: str
    status_updated: int
    type: str
    roster_ids: List[int] = []
    adds: Optional[Dict[str, int]] = None
    drops: Optional[Dict[str, int]] = None
    waiver_budget: List[WaiverBudget] = []
    draft_picks: List[TradedPicks] = []

class SleeperDraft(BaseSchema):
    draft_id: str
    league_id: str
    season: str
    draft_order: Optional[Dict[str, int]] = {}
    slot_to_roster_id: Optional[Dict[str, int]] = {}

class SleeperPlayer(BaseSchema):
    player_id: str
    position: Optional[str] = None
    team: Optional[str] = None
    first_name: str
    last_name: str
    years_exp: Optional[int] = None
    birth_date: Optional[str] = None

type PlayerMap = Dict[str, SleeperPlayer]

class TrendingPlayer(BaseSchema):
    player_id: str
    count: int

class NFLState(BaseSchema):
    season: str
    week: int

# --- Trade Signal Display Outbound Structures ---

class DisplayMovement(BaseSchema):
    name: str
    signal: Optional[str] = ""

class DisplayUser(BaseSchema):
    raw_display_name: str = Field(alias="display_name", repr=False)
    avatar: Optional[str] = None
    is_placeholder: bool = False
    adds: List[DisplayMovement] = []
    drops: List[DisplayMovement] = []

    @computed_field
    def display_name(self) -> str:
        if self.is_placeholder:
            return "Unknown User"
        return self.raw_display_name

class DisplayTransaction(BaseSchema):
    transaction_id: str
    time_ms: int
    league_name: str
    users: List[DisplayUser] = []

    class Config:
        from_attributes = True