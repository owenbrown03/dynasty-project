from pydantic import BaseModel
from typing import List, Optional, Dict

class CommissionerCutdownPlayer(BaseModel):
    player_id: str
    name: str
    position: Optional[str] = None
    team: Optional[str] = None
    ktc_value: Optional[float] = None

class CommissionerCutdownViolation(BaseModel):
    roster_id: int
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None
    owner_avatar: Optional[str] = None
    roster_size: int
    max_roster_size: int
    over_limit_count: int
    proposed_drops: List[CommissionerCutdownPlayer]

class CommissionerCutdownLeague(BaseModel):
    league_id: str
    league_name: str
    avatar: Optional[str] = None
    total_rosters: int
    max_roster_size: int
    violations: List[CommissionerCutdownViolation]

class CommissionerCutdownActionRequest(BaseModel):
    league_ids: List[str]
    action_type: str
    custom_message: Optional[str] = None
    selected_roster_ids: Optional[Dict[str, List[int]]] = None

class CommissionerCutdownActionResult(BaseModel):
    league_id: str
    roster_id: Optional[int] = None
    action: str
    success: bool
    details: Optional[str] = None
    error: Optional[str] = None

class CommissionerCutdownActionResponse(BaseModel):
    results: List[CommissionerCutdownActionResult]
