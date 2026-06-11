from typing import List, Optional
from app.schemas.base import Base

class TradeRequest(Base):
    league_id: str
    k_adds: List[str] = []
    v_adds: List[int] = []
    k_drops: List[str] = []
    v_drops: List[int] = []
    draft_picks: List[str] = []
    waiver_budget: Optional[List[int]] = None
    expires_at: Optional[int] = None

    def to_variables(self) -> dict:
        data = self.model_dump()
        data.pop("league_id", None)
        return data

class TradeResponse(Base):
    transaction_id: str

class WaiverRequest(Base):
    league_id: str
    k_adds: List[str] = []
    v_adds: List[int] = []
    k_drops: List[str] = []
    v_drops: List[int] = []
    k_settings: Optional[List[str]] = None
    v_settings: Optional[List[int]] = None

    def to_variables(self) -> dict:
        data = self.model_dump()
        data.pop("league_id", None)
        return data

class WaiverResponse(Base):
    transaction_id: str

class UpsertSleeperRequest(Base):
    sleeper_username: str