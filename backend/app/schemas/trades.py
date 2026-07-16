from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from app.schemas.base import Base


class TradeDirection(StrEnum):
    BUY = "buy"
    SELL = "sell"


class BulkTradePlayerSearchResult(Base):
    player_id: str

    name: str
    position: str | None = None
    team: str | None = None
    age: float | None = None

    ktc_value: int | None = None
    fc_value: int | None = None

    underdog_position_rank: str | None = None


class TradeDraftPickAsset(Base):
    """
    A current draft-pick asset.

    `og_roster_id` identifies the original team whose pick this is.
    `current_owner_roster_id` identifies who owns it right now.
    """

    season: str
    round: int

    og_roster_id: int
    current_owner_roster_id: int

    original_owner_name: str | None = None
    label: str


class BulkTradeCounterparty(Base):
    roster_id: int
    user_id: str | None = None
    name: str

    send_pick_choices: list["BulkTradePickChoice"] = Field(
        default_factory=list,
    )
    receive_pick_choices: list["BulkTradePickChoice"] = Field(
        default_factory=list,
    )


class BulkTradeLeagueAvailability(Base):
    league_id: str
    league_name: str
    league_avatar: str | None = None

    your_roster_id: int

    is_eligible: bool
    ineligibility_reason: str | None = None
    counterparty_options: list[BulkTradeCounterparty] = Field(
        default_factory=list,
    )


class BulkTradeAvailabilityResponse(Base):
    send_players: list[BulkTradePlayerSearchResult] = Field(
        default_factory=list,
    )
    send_picks: list["BulkTradePickRequest"] = Field(
        default_factory=list,
    )
    receive_players: list[BulkTradePlayerSearchResult] = Field(
        default_factory=list,
    )
    receive_picks: list["BulkTradePickRequest"] = Field(
        default_factory=list,
    )

    leagues: list[BulkTradeLeagueAvailability] = Field(
        default_factory=list,
    )


class BulkTradePickRequest(Base):
    season: str
    round: int


class BulkTradePickChoice(Base):
    request_index: int
    season: str
    round: int
    matching_picks: list[TradeDraftPickAsset] = Field(
        default_factory=list,
    )


class BulkTradePickReference(Base):
    """
    Frontend sends only the original-pick identity.

    The backend re-derives current ownership before proposing the trade.
    Never trust `current_owner_roster_id` from the frontend.
    """

    season: str
    round: int
    og_roster_id: int


class BulkTradeAvailabilityRequest(Base):
    send_player_ids: list[str] = Field(
        default_factory=list,
        max_length=8,
    )
    send_picks: list[BulkTradePickRequest] = Field(
        default_factory=list,
        max_length=8,
    )
    receive_player_ids: list[str] = Field(
        default_factory=list,
        max_length=8,
    )
    receive_picks: list[BulkTradePickRequest] = Field(
        default_factory=list,
        max_length=8,
    )


class BulkTradeOfferRequest(Base):
    league_id: str

    your_roster_id: int
    counterparty_roster_id: int

    send_player_ids: list[str] = Field(
        default_factory=list,
        max_length=8,
    )
    send_picks: list[BulkTradePickReference] = Field(
        default_factory=list,
        max_length=8,
    )
    receive_player_ids: list[str] = Field(
        default_factory=list,
        max_length=8,
    )
    receive_picks: list[BulkTradePickReference] = Field(
        default_factory=list,
        max_length=8,
    )

    expires_at: int | None = None


class BulkTradeProposalRequest(Base):
    offers: list[BulkTradeOfferRequest] = Field(
        min_length=1,
        max_length=50,
    )


class BulkTradeProposalResult(Base):
    league_id: str

    success: bool

    transaction_id: str | None = None
    error: str | None = None


class BulkTradeProposalResponse(Base):
    results: list[BulkTradeProposalResult] = Field(
        default_factory=list,
    )


class TradeCalculatorPickValueResponse(Base):
    season: str
    round: int
    slot: int | None = None
    total_rosters: int
    num_qbs: int
    ppr: int
    ktc_value: float | None = None
    fc_value: float | None = None
    rookie_war_value: float | None = None
