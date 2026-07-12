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
