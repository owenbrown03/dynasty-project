from app.schemas.base import Base


class DraftPickAsset(Base):
    season: str
    round: int
    og_roster_id: int
    current_owner_roster_id: int
    original_owner_name: str | None = None
    current_owner_name: str | None = None
    slot: int | None = None
    projected_slot: int | None = None
    slot_source_label: str | None = None
    label: str
    selected_value: float | None = None
    value_source_label: str | None = None
    rookie_war_value: float | None = None


class RookieWarHistoryRow(Base):
    player_id: str
    name: str
    position: str | None = None
    team: str | None = None
    draft_year: int
    round: int
    round_slot: int
    starter_war: float | None = None
    roster_war: float | None = None


class RookieWarHistoryResponse(Base):
    league_id: str | None = None
    league_name: str | None = None
    war_context: str
    has_war: bool
    rounds: list[int]
    rows: list[RookieWarHistoryRow]
