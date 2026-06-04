import uuid
from sqlmodel import SQLModel, Field
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional

class PlayerValue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    site_user_id: uuid.UUID = Field(sa_type=UUID(as_uuid=True), foreign_key="siteuser.id", index=True)
    player_id: str = Field(foreign_key="player.player_id", index=True)
    custom_market_value: float = Field(default=0.0)
    notes: Optional[str] = Field(default=None)