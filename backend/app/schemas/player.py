from pydantic import BaseModel
from typing import Optional


class PlayerMarketValue(BaseModel):
    player_id: str
    name: str

    ktc_value: Optional[int] = None
    fc_value: Optional[int] = None
    underdog_position_rank: Optional[str] = None
    war: Optional[float] = None