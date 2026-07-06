import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID


class SleeperConnection(SQLModel, table=True):
    __tablename__ = "sleeperconnection"

    id: Optional[int] = Field(default=None, primary_key=True)

    site_user_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(
            UUID(as_uuid=True),
            ForeignKey("siteuser.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
    )

    session_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            ForeignKey("usersession.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )

    sleeper_username: Optional[str] = Field(
        default=None,
        index=True,
    )

    sleeper_user_id: Optional[str] = Field(
        default=None,
        index=True,
    )

    encrypted_token: Optional[str] = Field(default=None)

    linked_at: datetime = Field(default_factory=datetime.now())