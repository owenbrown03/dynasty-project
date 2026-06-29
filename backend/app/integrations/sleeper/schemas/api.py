from pydantic import Field
from typing import List, Dict, Optional
from app.schemas.base import Base

class User(Base):
    user_id: str
    display_name: str
    avatar: Optional[str] = None
    is_owner: Optional[bool] = None

class LeagueSettings(Base):
    best_ball: Optional[bool] = False
    trade_deadline: Optional[int] = None
    type: int

class ScoringSettings(Base):
    bonus_rec_te: float = 0.0
    rec: float = 0.0
    pass_td: float = 0.0

class League(Base):
    league_id: str
    name: str
    total_rosters: int
    draft_id: str
    avatar: Optional[str] = None
    season: str    
    settings: Optional[LeagueSettings] = None
    scoring_settings: Optional[ScoringSettings] = None
    roster_positions: Optional[List[str]] = None

class RosterSettings(Base):
    fpts: Optional[int] = 0
    fpts_against: Optional[int] = 0
    wins: Optional[int] = 0
    ties: Optional[int] = 0
    losses: Optional[int] = 0

class Roster(Base):
    roster_id: int
    owner_id: Optional[str] = None 
    league_id: str
    players: Optional[List[str]] = None
    settings: RosterSettings

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

type PlayerMap = Dict[str, Player]

class TrendingPlayer(Base):
    player_id: str
    count: int

class NFLState(Base):
    season: str
    week: int

class ProjectionStats(Base):
    pts_ppr: float = 0
    pts_half_ppr: float = 0
    pts_std: float = 0
    gp: float = 0

class Projection(Base):
    player_id: str
    stats: ProjectionStats