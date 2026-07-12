from pydantic import Field

from app.schemas.base import Base


class FinanceLeagueSeasonEntry(Base):
    league_id: str
    league_name: str
    season: str
    total_rosters: int
    rank: int | None = None
    wins: int | None = None
    losses: int | None = None
    points_for: float | None = None
    buy_in_amount: float = 0.0
    winnings_amount: float = 0.0
    projected_winnings_amount: float = 0.0
    net_amount: float = 0.0


class FinanceSummaryResponse(Base):
    total_buy_ins: float = 0.0
    total_winnings: float = 0.0
    total_net: float = 0.0
    projected_current_winnings: float = 0.0
    seasons: list[FinanceLeagueSeasonEntry] = Field(
        default_factory=list,
    )


class FinanceLeagueSeasonUpdate(Base):
    league_id: str
    season: str
    buy_in_amount: float = 0.0
    winnings_amount: float = 0.0
