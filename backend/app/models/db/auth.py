import uuid
from datetime import datetime
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

    email_verified_at: Optional[datetime] = None
    verification_email_sent_at: Optional[datetime] = None
    
    settings: Dict[str, Any] = Field(
        default_factory=dict, 
        sa_type=JSON,
    )


class EmailVerificationToken(SQLModel, table=True):
    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    site_user_id: uuid.UUID = Field(
        sa_type=UUID(as_uuid=True),
        foreign_key="siteuser.id",
        index=True,
    )

    token_hash: str = Field(
        index=True,
        unique=True,
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
    )

    expires_at: datetime
    consumed_at: Optional[datetime] = None

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

    settings: Dict[str, Any] = Field(
        default_factory=dict,
        sa_type=JSON,
    )
