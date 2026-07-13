import uuid
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON, UniqueConstraint
from typing import Optional

class PlayerValue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    site_user_id: uuid.UUID = Field(sa_type=UUID(as_uuid=True), foreign_key="siteuser.id", index=True)
    player_id: str = Field(foreign_key="player.player_id", index=True)
    custom_market_value: float = Field(default=0.0)
    notes: Optional[str] = Field(default=None)


class PersonalProjection(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    site_user_id: uuid.UUID = Field(
        sa_type=UUID(as_uuid=True),
        foreign_key="siteuser.id",
        index=True,
    )
    player_id: str = Field(
        foreign_key="player.player_id",
        index=True,
    )
    season: int = Field(index=True)
    position: str = Field(index=True)
    default_source: str = Field(default="underdog")
    is_customized: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "site_user_id",
            "player_id",
            "season",
            name="uq_personalprojection_site_user_player_season",
        ),
    )


class PersonalProjectionOutcome(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    projection_id: int = Field(
        foreign_key="personalprojection.id",
        index=True,
    )
    outcome_index: int = Field(default=0)
    position_rank: int = Field(index=True)
    probability: float = Field(default=100.0)

    __table_args__ = (
        UniqueConstraint(
            "projection_id",
            "outcome_index",
            name="uq_personalprojectionoutcome_projection_index",
        ),
    )


class PersonalRankCurve(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    settings_fingerprint: str = Field(index=True)
    total_rosters: int = Field(default=12)
    scoring_settings: dict = Field(
        default_factory=dict,
        sa_type=JSON,
    )
    roster_positions: list[str] = Field(
        default_factory=list,
        sa_type=JSON,
    )
    season_start: int = Field(index=True)
    season_end: int = Field(index=True)
    position: str = Field(index=True)
    rank_value: int = Field(index=True)
    rank_band_start: int = Field(index=True)
    rank_band_end: int = Field(index=True)
    sample_size: int = Field(default=0)
    avg_redraft_starter_war: float = Field(default=0.0)
    avg_redraft_roster_war: float = Field(default=0.0)
    curve_version: str = Field(
        default="league_context_v1",
        index=True,
    )
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "settings_fingerprint",
            "position",
            "rank_value",
            "curve_version",
            name="uq_personalrankcurve_fingerprint_position_rank_version",
        ),
    )


class CommissionerLeagueNote(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    site_user_id: uuid.UUID = Field(
        sa_type=UUID(as_uuid=True),
        foreign_key="siteuser.id",
        index=True,
    )
    league_id: str = Field(
        foreign_key="league.league_id",
        index=True,
    )
    note: str = Field(default="")
    paid_years_ahead: int = Field(default=1)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "site_user_id",
            "league_id",
            name="uq_commissionerleaguenote_site_user_league",
        ),
    )


class CommissionerLeagueDues(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    site_user_id: uuid.UUID = Field(
        sa_type=UUID(as_uuid=True),
        foreign_key="siteuser.id",
        index=True,
    )
    league_id: str = Field(
        foreign_key="league.league_id",
        index=True,
    )
    roster_id: int = Field(index=True)
    season: str = Field(index=True)
    buy_in_amount: float | None = Field(default=None)
    is_paid: bool = Field(default=False)
    paid_at: datetime | None = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "site_user_id",
            "league_id",
            "roster_id",
            "season",
            name="uq_commissionerleaguedues_site_user_league_roster_season",
        ),
    )


class FinanceLeagueSeason(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    site_user_id: uuid.UUID = Field(
        sa_type=UUID(as_uuid=True),
        foreign_key="siteuser.id",
        index=True,
    )
    league_id: str = Field(
        foreign_key="league.league_id",
        index=True,
    )
    season: str = Field(index=True)
    buy_in_amount: float = Field(default=0.0)
    winnings_amount: float = Field(default=0.0)
    payout_structure: dict[str, float] = Field(
        default_factory=dict,
        sa_type=JSON,
    )
    is_excluded: bool = Field(default=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "site_user_id",
            "league_id",
            "season",
            name="uq_financeleagueseason_site_user_league_season",
        ),
    )


class FinanceUserDefaults(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    site_user_id: uuid.UUID = Field(
        sa_type=UUID(as_uuid=True),
        foreign_key="siteuser.id",
        index=True,
        unique=True,
    )
    buy_in_amount: float | None = Field(
        default=None,
        nullable=True,
    )
    payout_structure: dict[str, float] | None = Field(
        default=None,
        sa_type=JSON,
        nullable=True,
    )
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class FinanceLeagueDefault(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    site_user_id: uuid.UUID = Field(
        sa_type=UUID(as_uuid=True),
        foreign_key="siteuser.id",
        index=True,
    )
    league_family_id: str = Field(index=True)
    buy_in_amount: float | None = Field(
        default=None,
        nullable=True,
    )
    payout_structure: dict[str, float] | None = Field(
        default=None,
        sa_type=JSON,
        nullable=True,
    )
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "site_user_id",
            "league_family_id",
            name="uq_financeleaguedefault_site_user_family",
        ),
    )


class HiddenLeague(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    site_user_id: uuid.UUID = Field(
        sa_type=UUID(as_uuid=True),
        foreign_key="siteuser.id",
        index=True,
    )
    league_id: str = Field(
        foreign_key="league.league_id",
        index=True,
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "site_user_id",
            "league_id",
            name="uq_hiddenleague_site_user_league",
        ),
    )


class Reminder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    site_user_id: uuid.UUID = Field(
        sa_type=UUID(as_uuid=True),
        foreign_key="siteuser.id",
        index=True,
    )
    league_id: str | None = Field(
        default=None,
        foreign_key="league.league_id",
        index=True,
    )
    title: str
    note: str = Field(default="")
    due_week: int | None = Field(default=None, index=True)
    due_season: str | None = Field(default=None, index=True)
    delivery_channel: str = Field(default="in_app")
    completed: bool = Field(default=False)
    email_sent_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
