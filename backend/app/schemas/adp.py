from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.base import Base


class ADPFilters(Base):
    season: str | None = None
    draft_kind: str | None = None
    qb_format: str | None = None
    te_premium: str | None = None
    team_count: int | None = None
    scoring_format: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    minimum_draft_count: int = 5
    limit: int = 300


class ADPSample(Base):
    draft_count: int
    pick_count: int
    earliest_draft_at: datetime | None = None
    latest_draft_at: datetime | None = None
    generated_at: datetime


class ADPPlayerRow(Base):
    player_id: str
    name: str
    position: str | None = None
    team: str | None = None
    overall_adp: float
    median_pick: float
    min_pick: int
    max_pick: int
    standard_deviation: float | None = None
    pick_count: int
    draft_count: int
    selection_rate: float


class ADPResponse(Base):
    filters: ADPFilters
    sample: ADPSample
    players: list[ADPPlayerRow] = Field(default_factory=list)
