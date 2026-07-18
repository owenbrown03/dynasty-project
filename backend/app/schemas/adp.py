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
    data_source: str = "live"


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


class ADPDistributionItem(Base):
    key: str
    count: int


class ADPDatasetReport(Base):
    qualified_draft_count: int
    excluded_draft_count: int
    unique_league_count: int
    unique_root_source_count: int
    earliest_draft_at: datetime | None = None
    latest_draft_at: datetime | None = None
    qualification_code_distribution: list[ADPDistributionItem] = Field(
        default_factory=list,
    )
    draft_kind_distribution: list[ADPDistributionItem] = Field(
        default_factory=list,
    )
    qb_format_distribution: list[ADPDistributionItem] = Field(
        default_factory=list,
    )
    te_premium_distribution: list[ADPDistributionItem] = Field(
        default_factory=list,
    )
    scoring_format_distribution: list[ADPDistributionItem] = Field(
        default_factory=list,
    )
    team_count_distribution: list[ADPDistributionItem] = Field(
        default_factory=list,
    )
    discovery_depth_distribution: list[ADPDistributionItem] = Field(
        default_factory=list,
    )
    discovery_status_distribution: list[ADPDistributionItem] = Field(
        default_factory=list,
    )


class ADPMetadataResponse(Base):
    season_options: list[ADPDistributionItem] = Field(default_factory=list)
    draft_kind_options: list[ADPDistributionItem] = Field(default_factory=list)
    qb_format_options: list[ADPDistributionItem] = Field(default_factory=list)
    te_premium_options: list[ADPDistributionItem] = Field(default_factory=list)
    team_count_options: list[ADPDistributionItem] = Field(default_factory=list)
    scoring_format_options: list[ADPDistributionItem] = Field(default_factory=list)


class ADPDiscoveryStatus(Base):
    node_type: str
    node_value: str
    source_type: str | None = None
    source_value: str | None = None
    discovery_depth: int
    status: str
    attempt_count: int
    next_retry_at: datetime | None = None
    last_checked_at: datetime | None = None
    failure_reason: str | None = None
    updated_at: datetime


class ADPDiscoveryStatusResponse(Base):
    counts_by_status: list[ADPDistributionItem] = Field(default_factory=list)
    nodes: list[ADPDiscoveryStatus] = Field(default_factory=list)
