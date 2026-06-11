import uuid
from pydantic import EmailStr
from sqlmodel import SQLModel, Field, JSON
from sqlalchemy.dialects.postgresql import UUID
from typing import Dict, Any, Optional

class SiteUser(SQLModel, table=True):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, 
        primary_key=True, 
        sa_type=UUID(as_uuid=True),
    )

    email: EmailStr = Field(
        index=True, 
        unique=True,
    )

    hashed_password: str
    
    settings: Dict[str, Any] = Field(
        default_factory=dict, 
        sa_type=JSON,
    )

class UserSession(SQLModel, table=True):
    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    session_token: str = Field(
        index=True,
        unique=True,
    )

    site_user_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_type=UUID(as_uuid=True),
        foreign_key="siteuser.id",
    )

    sleeper_username: Optional[str] = None