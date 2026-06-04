import uuid
from sqlmodel import SQLModel, Field
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional
from datetime import datetime
from enum import Enum

class ConnectionSource(str, Enum):
    SESSION = "session"
    USER = "user"

class SleeperConnection(SQLModel, table=True):
    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    sleeper_user_id: Optional[str] = Field(
        default=None,
        index=True,
        unique=True,
    )

    encrypted_token: Optional[str] = Field(
        default=None,
    )

    site_user_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_type=UUID(as_uuid=True),
        foreign_key="siteuser.id",
        index=True,
    )

    session_id: Optional[int] = Field(
        default=None,
        foreign_key="usersession.id",
        index=True,
    )

    source: ConnectionSource = Field(
        default=ConnectionSource.SESSION,
    )

    linked_at: datetime = Field(
        default_factory=lambda: datetime.now(),
    )