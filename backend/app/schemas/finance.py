from pydantic import Field

from app.schemas.base import Base


class FinancePlacePayout(Base):
    place: int
    amount: float = 0.0


class FinanceLeagueSeasonEntry(Base):
    league_id: str
    league_family_id: str
    league_name: str
    season: str
    status: str
    total_rosters: int
    rank: int | None = None
    wins: int | None = None
    losses: int | None = None
    points_for: float | None = None
    finish_place: int | None = None
    projected_finish_place: int | None = None
    buy_in_amount: float = 0.0
    winnings_amount: float = 0.0
    payout_structure: list[FinancePlacePayout] = Field(
        default_factory=list,
    )
    buy_in_source: str = "none"
    payout_source: str = "none"
    has_season_override: bool = False
    has_league_default: bool = False
    is_excluded: bool = False
    projected_winnings_amount: float = 0.0
    projected_winnings_source: str = "heuristic"
    net_amount: float = 0.0


class FinanceDefaultSettings(Base):
    buy_in_amount: float | None = None
    payout_structure: list[FinancePlacePayout] = Field(
        default_factory=list,
    )


class FinanceLeagueDefaultEntry(Base):
    league_family_id: str
    league_name: str
    buy_in_amount: float | None = None
    payout_structure: list[FinancePlacePayout] = Field(
        default_factory=list,
    )


class FinanceSummaryResponse(Base):
    total_buy_ins: float = 0.0
    total_winnings: float = 0.0
    total_net: float = 0.0
    projected_current_winnings: float = 0.0
    defaults: FinanceDefaultSettings = Field(
        default_factory=FinanceDefaultSettings,
    )
    league_defaults: list[FinanceLeagueDefaultEntry] = Field(
        default_factory=list,
    )
    seasons: list[FinanceLeagueSeasonEntry] = Field(
        default_factory=list,
    )


class FinanceLeagueSeasonUpdate(Base):
    league_id: str
    season: str
    buy_in_amount: float = 0.0
    payout_structure: list[FinancePlacePayout] = Field(
        default_factory=list,
    )
    is_excluded: bool = False


class FinanceSeasonReset(Base):
    league_id: str
    season: str


class FinanceDefaultsUpdate(Base):
    buy_in_amount: float | None = None
    payout_structure: list[FinancePlacePayout] = Field(
        default_factory=list,
    )


class FinanceLeagueDefaultsUpdate(FinanceDefaultsUpdate):
    league_family_ids: list[str] = Field(
        default_factory=list,
    )
