from __future__ import annotations

from app.schemas.base import Base


class PersonalValueSearchResult(Base):
    player_id: str
    name: str
    position: str | None
    team: str | None
    age: float | None = None
    underdog_position_rank: str | None = None
    ktc_value: float | None = None
    fc_value: float | None = None
    dynasty_roster_war: float | None = None


class PersonalValueLeagueContext(Base):
    league_id: str
    league_name: str
    season: int
    total_rosters: int


class PersonalProjectionOutcomeItem(Base):
    position_rank: int
    probability: float


class PersonalProjectionSeasonItem(Base):
    season: int
    outcomes: list[PersonalProjectionOutcomeItem]
    default_position_rank: int | None = None
    is_customized: bool = False


class PersonalValueMetrics(Base):
    redraft_starter_war: float | None = None
    redraft_roster_war: float | None = None
    dynasty_starter_war: float | None = None
    dynasty_roster_war: float | None = None


class PersonalValuePlayer(Base):
    player_id: str
    name: str
    position: str
    team: str | None = None
    age: float | None = None
    underdog_position_rank: str | None = None


class PersonalValueDetailResponse(Base):
    context: PersonalValueLeagueContext
    player: PersonalValuePlayer
    market_values: PersonalValueMetrics
    custom_values: PersonalValueMetrics
    delta_values: PersonalValueMetrics
    seasons: list[PersonalProjectionSeasonItem]


class PersonalValuePoolItem(Base):
    player: PersonalValuePlayer
    market_values: PersonalValueMetrics
    custom_values: PersonalValueMetrics
    delta_values: PersonalValueMetrics
    is_customized: bool = False


class PersonalValuePoolGroup(Base):
    position: str
    players: list[PersonalValuePoolItem]


class PersonalValuePoolResponse(Base):
    context: PersonalValueLeagueContext
    groups: list[PersonalValuePoolGroup]


class PersonalProjectionSeasonUpdate(Base):
    season: int
    outcomes: list[PersonalProjectionOutcomeItem]


class PersonalValueUpdateRequest(Base):
    seasons: list[PersonalProjectionSeasonUpdate]
