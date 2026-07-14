from pydantic import BaseModel


class LeagueSettingsDetail(BaseModel):
    label: str
    value: str


class LeagueOwner(BaseModel):
    user_id: str | None = None
    display_name: str
    avatar: str | None = None


class LeaguePick(BaseModel):
    season: str
    round: int
    og_roster_id: int
    current_owner_roster_id: int
    label: str
    slot: int | None = None
    projected_slot: int | None = None
    slot_source_label: str | None = None
    fc_value: float | None = None
    ktc_value: float | None = None


class LeaguePlayer(BaseModel):
    player_id: str
    name: str
    position: str | None = None
    team: str | None = None
    age: float | None = None
    underdog_position_rank: str | None = None
    projected_points: float | None = None
    ktc_value: int | None = None
    fc_value: int | None = None
    fc_trend_30_day: int | None = None
    redraft_starter_war: float | None = None
    redraft_roster_war: float | None = None
    dynasty_starter_war: float | None = None
    dynasty_roster_war: float | None = None
    my_redraft_starter_war: float | None = None
    my_redraft_roster_war: float | None = None
    my_dynasty_starter_war: float | None = None
    my_dynasty_roster_war: float | None = None
    is_starter: bool = False


class LeagueRoster(BaseModel):
    roster_id: int
    owner: LeagueOwner
    rank: int
    record: str
    wins: int
    losses: int
    ties: int
    actual_points_for: float
    projected_points: float
    faab_remaining: int
    waiver_position: int
    total_moves: int
    open_roster_spots: int
    average_age: float | None = None
    total_ktc_value: float
    total_fc_value: float
    total_redraft_starter_war: float
    total_redraft_roster_war: float
    total_dynasty_starter_war: float
    total_dynasty_roster_war: float
    total_pick_ktc_value: float
    total_pick_fc_value: float
    total_asset_ktc_value: float
    total_asset_fc_value: float
    players: list[LeaguePlayer]
    picks: list[LeaguePick]


class LeagueDetailsResponse(BaseModel):
    league_id: str
    league_name: str
    avatar: str | None = None
    season: str
    total_rosters: int
    note: str = ""
    draft_pick_projection_summary: str | None = None
    settings_badges: list[str]
    settings_details: list[LeagueSettingsDetail]
    war_position_history: list["LeagueWarPositionSeason"] = []
    war_player_history: list["LeagueWarPlayerSeason"] = []
    rosters: list[LeagueRoster]


class LeagueWarPositionValue(BaseModel):
    position: str
    war: float


class LeagueWarPositionSeason(BaseModel):
    season: str
    source: str
    values: list[LeagueWarPositionValue]


class LeagueWarPlayerPoint(BaseModel):
    player_id: str
    name: str
    position: str
    war: float
    rank: int


class LeagueWarPlayerSeason(BaseModel):
    season: str
    source: str
    war_type: str
    players: list[LeagueWarPlayerPoint]
