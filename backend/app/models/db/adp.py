from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class ADPDiscoveryNode(SQLModel, table=True):
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
    )
    node_type: str = Field(index=True)
    node_value: str = Field(index=True)
    source_type: str | None = Field(
        default=None,
        nullable=True,
    )
    source_value: str | None = Field(
        default=None,
        nullable=True,
    )
    discovery_depth: int = Field(default=0, index=True)
    status: str = Field(default="pending", index=True)
    attempt_count: int = Field(default=0)
    next_retry_at: datetime | None = Field(
        default=None,
        nullable=True,
        index=True,
    )
    last_checked_at: datetime | None = Field(
        default=None,
        nullable=True,
    )
    failure_reason: str | None = Field(
        default=None,
        nullable=True,
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ADPDraftQualification(SQLModel, table=True):
    draft_id: str = Field(
        primary_key=True,
        foreign_key="draft.draft_id",
    )
    league_id: str | None = Field(
        default=None,
        foreign_key="league.league_id",
        nullable=True,
        index=True,
    )
    draft_started_at: datetime | None = Field(
        default=None,
        nullable=True,
        index=True,
    )
    draft_completed_at: datetime | None = Field(
        default=None,
        nullable=True,
        index=True,
    )
    draft_kind: str = Field(default="unknown", index=True)
    league_format: str = Field(default="unknown", index=True)
    qb_format: str = Field(default="unknown", index=True)
    te_premium: str = Field(default="unknown", index=True)
    scoring_format: str = Field(default="unknown", index=True)
    team_count: int | None = Field(
        default=None,
        nullable=True,
        index=True,
    )
    round_count: int | None = Field(
        default=None,
        nullable=True,
    )
    is_mock: bool = Field(default=False, nullable=False)
    is_complete: bool = Field(default=False, nullable=False)
    is_qualified: bool = Field(default=False, nullable=False, index=True)
    qualification_code: str = Field(
        default="unknown_format",
        index=True,
    )
    qualification_details: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )
    classified_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
