from datetime import datetime

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
