from typing import Optional
from pydantic import BaseModel


class KTCPlayer(BaseModel):
    player_name: str
    position: str
    position_rank: str        # e.g. "WR1", "QB3", "PICK"
    team: Optional[str]
    age: Optional[float]
    value: int                # 0-9999 KTC score
    is_rookie: bool
    sf_value: Optional[int] = None
    sf_position_rank: Optional[str] = None
    redraft_value: Optional[int] = None
    redraft_position_rank: Optional[str] = None
    sf_redraft_value: Optional[int] = None
    sf_redraft_position_rank: Optional[str] = None
