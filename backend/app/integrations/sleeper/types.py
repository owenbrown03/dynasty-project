from typing import List, Optional
from pydantic import Field

from app.schemas.base import Base

class TradeRequest(Base):
    league_id: str
    k_adds: List[str] = Field(default_factory=list)
    v_adds: List[int] = Field(default_factory=list)
    k_drops: List[str] = Field(default_factory=list)
    v_drops: List[int] = Field(default_factory=list)
    draft_picks: List[str] = Field(default_factory=list)
    waiver_budget: Optional[List[int]] = None
    expires_at: Optional[int] = None

    def to_variables(self) -> dict:
        data = self.model_dump()
        data.pop("league_id", None)
        return data

class TradeResponse(Base):
    transaction_id: str

class UpsertSleeperRequest(Base):
    sleeper_username: str
