import uuid
from pydantic import EmailStr
from sqlmodel import SQLModel, Field, JSON
from sqlalchemy.dialects.postgresql import UUID
from typing import Dict, Any, Optional

class SiteUser(SQLModel, table=True):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, 
        primary_key=True, 
        sa_type=UUID(as_uuid=True)
    )
    email: EmailStr = Field(index=True, unique=True)
    hashed_password: str
    sleeper_id: Optional[str] = Field(default=None, index=True)
    settings: Dict[str, Any] = Field(default_factory=dict, sa_type=JSON)

class UserSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_token: str = Field(index=True)
    site_user_id: uuid.UUID = Field(sa_type=UUID(as_uuid=True), foreign_key="siteuser.id")

class PlayerValue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    site_user_id: uuid.UUID = Field(sa_type=UUID(as_uuid=True), foreign_key="siteuser.id", index=True)
    player_id: str = Field(foreign_key="player.player_id", index=True)
    custom_market_value: float = Field(default=0.0)
    notes: Optional[str] = Field(default=None)