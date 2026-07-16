from pydantic import Field

from app.schemas.base import Base
from app.schemas.player import PlayerValue
from app.services.values.basis import ValueBasis


class WaiverLeagueOverview(Base):
    league_id: str
    league_name: str
    league_avatar: str | None = None

    roster_id: int

    roster_size: int
    roster_capacity: int
    roster_spots_available: int

    faab_budget: int
    faab_used: int
    faab_remaining: int
    faab_percent_remaining: float

    available_player_count: int

    value_basis: ValueBasis
    value_label: str

    suggested_add: PlayerValue | None = None
    suggested_drop: PlayerValue | None = None

    suggested_add_value: float | None = None
    suggested_drop_value: float | None = None
    value_gain: float | None = None

    can_submit_claim: bool


class WaiverOverviewResponse(Base):
    sleeper_username: str | None = None

    leagues: list[WaiverLeagueOverview] = Field(
        default_factory=list
    )


class WaiverClaimRequest(Base):
    league_id: str
    roster_id: int

    add_player_id: str
    drop_player_id: str | None = None

    bid: int = Field(default=0, ge=0)


class WaiverClaimResponse(Base):
    transaction_id: str


class WaiverLeagueOption(Base):
    league_id: str
    league_name: str
    league_avatar: str | None = None

    roster_id: int

    roster_size: int
    roster_capacity: int
    roster_spots_available: int

    faab_remaining: int
    faab_percent_remaining: float


class WaiverAvailableLeagueAvailability(Base):
    league_id: str
    league_name: str
    league_avatar: str | None = None

    roster_id: int
    roster_size: int
    roster_capacity: int
    roster_spots_available: int

    faab_remaining: int
    faab_percent_remaining: float

    can_submit_claim: bool = True
    claim_blocked_reason: str | None = None

    selected_value: float | None = None


class WaiverAvailablePlayer(PlayerValue):
    league_id: str | None = None
    league_name: str | None = None
    league_avatar: str | None = None

    roster_id: int | None = None
    roster_size: int | None = None
    roster_capacity: int | None = None
    roster_spots_available: int | None = None

    faab_remaining: int | None = None
    faab_percent_remaining: float | None = None

    can_submit_claim: bool = True
    claim_blocked_reason: str | None = None

    league_count: int = 1
    league_availability: list[
        WaiverAvailableLeagueAvailability
    ] = Field(default_factory=list)

    selected_value: float | None = None


class WaiverAvailablePlayersResponse(Base):
    league_id: str | None = None
    league_name: str
    league_avatar: str | None = None

    roster_id: int | None = None
    is_all_leagues: bool = False

    value_basis: ValueBasis
    value_label: str

    page: int = 1
    page_size: int = 50
    total_pages: int = 0
    total_players: int

    players: list[WaiverAvailablePlayer] = Field(
        default_factory=list,
    )


class WaiverRosterPlayer(PlayerValue):
    selected_value: float | None = None


class WaiverRosterPlayersResponse(Base):
    league_id: str
    league_name: str

    roster_id: int

    value_basis: ValueBasis
    value_label: str

    total_players: int

    players: list[WaiverRosterPlayer] = Field(
        default_factory=list,
    )


class WaiverRecentlyDroppedPlayer(PlayerValue):
    transaction_id: str
    dropped_at_ms: int

    league_id: str
    league_name: str
    league_avatar: str | None = None

    roster_id: int

    roster_spots_available: int
    faab_remaining: int
    faab_percent_remaining: float

    can_submit_claim: bool
    claim_blocked_reason: str | None = None

    selected_value: float | None = None


class WaiverRecentlyDroppedResponse(Base):
    sleeper_username: str | None = None

    value_basis: ValueBasis
    value_label: str

    sync_requested: bool = False

    page: int = 1
    page_size: int = 50
    total_pages: int = 0
    total_players: int

    players: list[WaiverRecentlyDroppedPlayer] = Field(
        default_factory=list,
    )


class BulkWaiverPlayerSearchResult(Base):
    player_id: str

    name: str
    position: str | None
    team: str | None
    age: float | None = None

    ktc_value: int | None = None
    fc_value: int | None = None

    underdog_position_rank: str | None = None


class BulkWaiverLeagueAvailability(Base):
    league_id: str
    league_name: str
    league_avatar: str | None = None

    roster_id: int

    is_available: bool
    already_rostered_by_you: bool = False
    unavailable_reason: str | None = None

    can_submit_claim: bool
    claim_blocked_reason: str | None = None

    faab_remaining: int
    roster_spots_available: int
    requires_drop: bool

    add_selected_value: float | None = None

    recommended_drop: PlayerValue | None = None
    recommended_drop_selected_value: float | None = None


class BulkWaiverAvailabilityResponse(Base):
    player: BulkWaiverPlayerSearchResult

    value_basis: ValueBasis
    value_label: str

    leagues: list[BulkWaiverLeagueAvailability] = Field(
        default_factory=list,
    )


class BulkWaiverClaimRequest(Base):
    claims: list[WaiverClaimRequest] = Field(
        min_length=1,
        max_length=50,
    )


class BulkWaiverClaimResult(Base):
    league_id: str
    roster_id: int

    success: bool

    transaction_id: str | None = None
    error: str | None = None


class BulkWaiverClaimResponse(Base):
    results: list[BulkWaiverClaimResult] = Field(
        default_factory=list,
    )
