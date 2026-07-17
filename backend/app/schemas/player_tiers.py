from app.schemas.base import Base
from app.services.values.basis import ValueBasis


class TierPlayer(Base):
    player_id: str
    name: str
    position: str | None
    team: str | None
    age: float | None = None
    rank: int
    tier: str
    selected_value: float
    exposure_pct: float | None = None
    exposure_owned_leagues: int | None = None
    exposure_total_leagues: int | None = None


class TierGroup(Base):
    label: str
    players: list[TierPlayer]


class PlayerTierBoardResponse(Base):
    value_basis: ValueBasis
    value_label: str
    season: int
    war_context: str
    war_league_id: str | None = None
    war_league_name: str | None = None
    tiers: list[TierGroup]
