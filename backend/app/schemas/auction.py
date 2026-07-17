from pydantic import BaseModel, Field


class AuctionDraftPositionSummary(BaseModel):
    position: str
    target_count: int
    drafted_count: int
    spent_amount: int
    spent_budget_pct: float
    selected_value_total: float


class AuctionDraftPlayerAsset(BaseModel):
    player_id: str
    name: str
    position: str | None = None
    team: str | None = None
    age: float | None = None
    underdog_position_rank: str | None = None
    selected_value: float | None = None
    amount_paid: int = 0
    budget_pct: float = 0.0
    value_per_dollar: float | None = None


class AuctionAvailablePlayerAsset(BaseModel):
    player_id: str
    name: str
    position: str | None = None
    team: str | None = None
    age: float | None = None
    underdog_position_rank: str | None = None
    selected_value: float | None = None
    fair_market_price: int
    suggested_max_bid: int
    need_multiplier: float


class AuctionDraftTeamSummary(BaseModel):
    roster_id: int
    owner_name: str
    owner_avatar: str | None = None
    players_drafted: int
    roster_spots_left: int
    spent_amount: int
    spent_budget_pct: float
    remaining_budget: int
    max_bid: int
    acquired_value: float
    value_per_dollar: float | None = None


class AuctionDraftMyTeam(BaseModel):
    roster_id: int
    owner_name: str
    owner_avatar: str | None = None
    spent_amount: int
    spent_budget_pct: float
    remaining_budget: int
    max_bid: int
    roster_size_target: int
    players_drafted: int
    roster_spots_left: int
    acquired_value: float
    drafted_players: list[AuctionDraftPlayerAsset] = Field(
        default_factory=list,
    )
    position_summaries: list[AuctionDraftPositionSummary] = Field(
        default_factory=list,
    )


class AuctionDraftResponse(BaseModel):
    draft_id: str
    league_id: str
    league_name: str
    league_avatar: str | None = None
    season: str
    draft_status: str | None = None
    draft_type: str | None = None
    auction_budget: int
    total_budget: int
    spent_budget: int
    remaining_budget: int
    value_basis: str
    value_label: str
    search: str | None = None
    page: int = 1
    page_size: int = 75
    total_available_players: int = 0
    my_team: AuctionDraftMyTeam
    league_targets: list[AuctionDraftPositionSummary] = Field(
        default_factory=list,
    )
    team_summaries: list[AuctionDraftTeamSummary] = Field(
        default_factory=list,
    )
    available_players: list[AuctionAvailablePlayerAsset] = Field(
        default_factory=list,
    )
