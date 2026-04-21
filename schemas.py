from pydantic import BaseModel, Field, ConfigDict

class SleeperBase(BaseModel):
    model_config = ConfigDict(
            from_attributes=True, 
            extra='ignore'
        )

class SleeperUser(SleeperBase):
    user_id: str
    display_name: str
    avatar: str | None = None
    is_owner: bool | None = None

class LeagueSettings(SleeperBase):
    best_ball: bool
    trade_deadline: int | None = None

class ScoringSettings(SleeperBase):
    bonus_rec_te: float = 0.0
    rec: float = 0.0
    pass_td: float = 0.0

class SleeperLeague(SleeperBase):
    league_id: str
    name: str
    total_rosters: int
    draft_id: str
    avatar: str | None = None
    season: str    
    settings: LeagueSettings
    scoring_settings: ScoringSettings
    roster_positions: list[str]

class RosterSettings(SleeperBase):
    fpts: int | None = 0
    fpts_against: int | None = 0
    wins: int | None = 0
    ties: int | None = 0
    losses: int | None = 0

class SleeperRoster(SleeperBase):
    roster_id: int
    owner_id: str | None = None # also known as user_id
    league_id: str
    players: list[str] | None = None
    settings: RosterSettings

class BracketSource(SleeperBase):
    # 'w' means 'winner of match ID', 'l' means 'loser of match ID'
    w: int | None = None 
    l: int | None = None 

class SleeperMatchup(SleeperBase):
    r: int = Field(..., alias="r")  # Round
    m: int = Field(..., alias="m")  # Match ID
    t1: int | None = None        # Team 1 ID
    t2: int | None = None        # Team 2 ID
    
    # These show where the teams come from in later rounds
    t1_from: BracketSource | None = None
    t2_from: BracketSource | None = None
    
    w: int | None = None         # Winner ID
    l: int | None = None        # Loser ID
    p: int | None = None         # Potentially 'place' (e.g., 1st, 3rd, 5th)

class WaiverBudget(SleeperBase):
    sender: int
    receiver: int
    amount: int  

class TradedPicks(SleeperBase):
    season: str
    round: int
    roster_id: int
    previous_owner_id: int
    owner_id: int

class SleeperTransaction(SleeperBase):
    transaction_id: str
    status_updated: int
    type: str
    roster_ids: list[int] = []
    adds: dict[str, int] | None = None
    drops: dict[str, int] | None = None
    waiver_budget: list[WaiverBudget] = []
    draft_picks: list[TradedPicks] = []

class SleeperDraft(SleeperBase):
    draft_id: str
    league_id: str
    draft_order: dict[str, int] | None = {}
    slot_to_roster_id: dict[str, int] | None = {}

class SleeperPlayer(SleeperBase):
    position: str
    team: str | None = None
    first_name: str
    last_name: str
    age: int
    player_id: str
    years_exp: str

type PlayerMap = dict[str, SleeperPlayer]

class TrendingPlayer(SleeperBase):
    player_id: str
    count: int

class NFLState(SleeperBase):
    season: str
    week: int