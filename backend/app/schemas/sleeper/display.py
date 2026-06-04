from pydantic import Field, computed_field
from typing import List, Optional
from app.schemas.base import Base

class Movement(Base):
    name: str
    signal: Optional[str] = ""

class User(Base):
    raw_display_name: str = Field(alias="display_name", repr=False)
    avatar: Optional[str] = None
    is_placeholder: bool = False
    adds: List[Movement] = []
    drops: List[Movement] = []

    @computed_field
    def display_name(self) -> str:
        if self.is_placeholder:
            return "Unknown User"
        return self.raw_display_name

class Transaction(Base):
    transaction_id: str
    time_ms: int
    league_name: str
    users: List[User] = []

    class Config:
        from_attributes = True