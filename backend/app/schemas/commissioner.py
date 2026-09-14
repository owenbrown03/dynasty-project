from datetime import datetime
from typing import Dict, List, Optional
from pydantic import Field, field_validator

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

class CommissionerFaabRosterInfo(Base):
    roster_id: int
    owner_name: str | None
    owner_avatar: str | None
    current_budget: int
    budget_used: int

class CommissionerFaabLeagueInfo(Base):
    league_id: str
    league_name: str
    avatar: str | None
    default_budget: int
    total_rosters: int
    rosters_with_spent_faab: int
    rosters: list[CommissionerFaabRosterInfo]

class CommissionerFaabResetRequest(Base):
    league_ids: list[str]
    target_budget: int | None = None

class CommissionerFaabResetResult(Base):
    league_id: str
    league_name: str
    rosters_reset: int
    success: bool
    error: str | None

class CommissionerFaabResetResponse(Base):
    total_leagues: int
    successful_leagues: int
    results: list[CommissionerFaabResetResult]

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


class CommissionerWaiverDaySchedule(Base):
    day: str
    setting: int  # 0=FA, 1=Waivers, 2=Locked, 3=Waivers->FA


class CommissionerWaiverLeagueInfo(Base):
    league_id: str
    league_name: str
    avatar: str | None = None
    total_rosters: int = 0
    daily_waivers: int = 0
    daily_waivers_hour: int = 0
    daily_waivers_days: int = 5461
    daily_waivers_days_b4: str = "1111111"
    waiver_type: int = 2
    waiver_clear_days: int = 2
    waiver_day_of_week: int = 2
    schedule: list[CommissionerWaiverDaySchedule] = Field(default_factory=list)


class CommissionerWaiverUpdateRequest(Base):
    league_ids: list[str]
    daily_waivers: int = 1
    daily_waivers_days: int | None = None
    sunday_to_saturday_settings: list[int] | None = None  # 7 ints (0..3) [Sun, Mon, Tue, Wed, Thu, Fri, Sat]
    daily_waivers_hour: int | None = None  # 0..23, or None to preserve each league's existing hour
    waiver_clear_days: int | None = None  # 0..3, or None to preserve each league's setting
    waiver_day_of_week: int | None = None  # 1=Tue, 2=Wed, etc., or None to preserve each league's setting



class CommissionerWaiverUpdateResult(Base):
    league_id: str
    league_name: str
    success: bool
    error: str | None = None


class CommissionerWaiverUpdateResponse(Base):
    total_leagues: int
    successful_leagues: int
    results: list[CommissionerWaiverUpdateResult]


class CommissionerStandardWaiverPreset(Base):
    sunday_to_saturday_settings: list[int] = Field(
        default=[3, 0, 1, 1, 3, 3, 3],
        description="7 ints (0..3) [Sun, Mon, Tue, Wed, Thu, Fri, Sat]",
    )
    daily_waivers_hour: int | None = None
    daily_waivers: int = 1
    is_custom: bool = False


class CommissionerStandardWaiverPresetUpdate(Base):
    sunday_to_saturday_settings: list[int] = Field(
        description="7 ints (0..3) [Sun, Mon, Tue, Wed, Thu, Fri, Sat]",
    )
    daily_waivers_hour: int | None = None
    daily_waivers: int = 1

    @field_validator("sunday_to_saturday_settings")
    @classmethod
    def validate_days(cls, v: list[int]) -> list[int]:
        if len(v) != 7 or any(d < 0 or d > 3 for d in v):
            raise ValueError("sunday_to_saturday_settings must have exactly 7 integers between 0 and 3")
        return v


class CommissionerLeagueSettingsInfo(Base):
    league_id: str
    league_name: str
    avatar: str | None = None
    total_rosters: int = 0
    best_ball: int = 0

    # Roster & Drop Rules
    bench_lock: int = 0  # 0=Allow bench drop after kickoff, 1=Prevent bench drop
    disable_adds: int = 0  # 0=Adds allowed, 1=Adds locked
    offseason_adds: int = 0  # 0=Locked in offseason, 1=Allowed in offseason

    # Trading
    disable_trades: int = 0  # 0=Trades allowed, 1=Trades disabled
    trade_deadline: int = 11  # Week number 9..14, or 99 for No deadline
    pick_trading: int = 1  # 0=Disabled, 1=Enabled
    trade_review_days: int = 0  # 0=None, 1..3 days
    veto_auto_poll: int = 0  # 0=Off, 1=On
    veto_show_votes: int = 0  # 0=Hidden, 1=Visible
    veto_votes_needed: int = 0

    # Matchups & Playoffs
    playoff_teams: int = 6
    playoff_week_start: int = 15
    league_average_match: int = 0  # 0=Off, 1=On (median match)

    # Waivers
    waiver_bid_min: int = 0  # 0=$0 min, 1=$1 min

    # Taxi
    taxi_deadline: int = 0  # 0=None, 1..18
    taxi_allow_vets: int = 0  # 0=Rookies only, 1=Rookies & Vets
    taxi_years: int = 0  # 0=Any, 1..4 years

    # IR / Reserve
    reserve_allow_out: int = 1
    reserve_allow_doubtful: int = 0
    reserve_allow_sus: int = 0
    reserve_allow_cov: int = 0
    reserve_allow_na: int = 0
    reserve_allow_dnr: int = 0


class CommissionerSettingsUpdateRequest(Base):
    league_ids: list[str]

    # Optional fields: None = Keep Current League Setting
    bench_lock: int | None = None
    disable_adds: int | None = None
    offseason_adds: int | None = None

    disable_trades: int | None = None
    trade_deadline: int | None = None
    pick_trading: int | None = None
    trade_review_days: int | None = None
    veto_auto_poll: int | None = None
    veto_show_votes: int | None = None
    veto_votes_needed: int | None = None

    playoff_teams: int | None = None
    playoff_week_start: int | None = None
    league_average_match: int | None = None

    waiver_bid_min: int | None = None

    taxi_deadline: int | None = None
    taxi_allow_vets: int | None = None
    taxi_years: int | None = None

    reserve_allow_out: int | None = None
    reserve_allow_doubtful: int | None = None
    reserve_allow_sus: int | None = None
    reserve_allow_cov: int | None = None
    reserve_allow_na: int | None = None
    reserve_allow_dnr: int | None = None


class CommissionerSettingsUpdateResult(Base):
    league_id: str
    league_name: str
    success: bool
    error: str | None = None


class CommissionerSettingsUpdateResponse(Base):
    total_leagues: int
    successful_leagues: int
    results: list[CommissionerSettingsUpdateResult]


