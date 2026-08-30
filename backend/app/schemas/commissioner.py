from datetime import datetime
from typing import Dict, List, Optional
from pydantic import Field

from app.schemas.base import Base
from app.schemas.draft import DraftPickAsset
from app.services.values.basis import ValueBasis


class CommissionerPlayerAsset(Base):
    player_id: str
    name: str
    position: str | None = None
    team: str | None = None
    age: float | None = None
    selected_value: float | None = None


class CommissionerLineupSlot(Base):
    slot: str
    player: CommissionerPlayerAsset | None = None


class CommissionerOrphanRoster(Base):
    league_id: str
    league_name: str
    league_season: str
    roster_id: int
    roster_name: str

    settings_badges: list[str] = Field(
        default_factory=list,
    )

    roster_value: float = 0.0
    league_average_value: float = 0.0
    average_age: float | None = None

    lineup: list[CommissionerLineupSlot] = Field(
        default_factory=list,
    )
    bench: list[CommissionerPlayerAsset] = Field(
        default_factory=list,
    )
    picks: list[DraftPickAsset] = Field(
        default_factory=list,
    )


class CommissionerOrphansResponse(Base):
    username: str
    value_basis: ValueBasis
    value_label: str
    orphans: list[CommissionerOrphanRoster] = Field(
        default_factory=list,
    )


class CommissionerLeagueDuesEntry(Base):
    league_id: str
    roster_id: int
    roster_name: str
    season: str
    traded_pick_count: int = 0
    traded_pick_labels: list[str] = Field(
        default_factory=list,
    )
    buy_in_amount: float | None = None
    is_paid: bool = False
    paid_at: datetime | None = None


class CommissionerWorkspaceLeague(Base):
    league_id: str
    league_name: str
    league_season: str
    note: str = ""
    paid_years_ahead: int = 1
    dues: list[CommissionerLeagueDuesEntry] = Field(
        default_factory=list,
    )


class CommissionerWorkspaceResponse(Base):
    leagues: list[CommissionerWorkspaceLeague] = Field(
        default_factory=list,
    )


class CommissionerLeagueNoteUpdate(Base):
    league_id: str
    note: str = ""


class CommissionerLeagueDuesUpdate(Base):
    league_id: str
    roster_id: int
    season: str
    buy_in_amount: float | None = None
    is_paid: bool = False


class CommissionerLeagueSettingsUpdate(Base):
    league_id: str
    paid_years_ahead: int = 1


class CommissionerCutdownPlayer(Base):
    player_id: str
    name: str
    position: Optional[str] = None
    team: Optional[str] = None
    ktc_value: Optional[float] = None


class CommissionerCutdownViolation(Base):
    roster_id: int
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None
    owner_avatar: Optional[str] = None
    roster_size: int
    max_roster_size: int
    over_limit_count: int
    proposed_drops: List[CommissionerCutdownPlayer]


class CommissionerCutdownLeague(Base):
    league_id: str
    league_name: str
    avatar: Optional[str] = None
    total_rosters: int
    max_roster_size: int
    violations: List[CommissionerCutdownViolation]


class CommissionerCutdownActionRequest(Base):
    league_ids: List[str]
    action_type: str
    custom_message: Optional[str] = None
    selected_roster_ids: Optional[Dict[str, List[int]]] = None


class CommissionerCutdownActionResult(Base):
    league_id: str
    roster_id: Optional[int] = None
    action: str
    success: bool
    details: Optional[str] = None
    error: Optional[str] = None


class CommissionerCutdownActionResponse(Base):
    results: List[CommissionerCutdownActionResult]


class CommissionerPollBroadcastRequest(Base):
    prompt: str
    choices: list[str]
    is_private: bool = True
    poll_type: str | None = None
    expiration_days: int | None = 7
    follow_up_message: str | None = None
    league_ids: list[str]


class CommissionerPollBroadcastResult(Base):
    league_id: str
    league_name: str | None = None
    poll_id: str | None = None
    success: bool
    error: str | None = None


class CommissionerPollBroadcastResponse(Base):
    total_leagues: int
    successful_leagues: int
    results: list[CommissionerPollBroadcastResult]

