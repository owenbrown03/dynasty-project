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
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "site_user_id",
            "league_id",
            "season",
            name="uq_financeleagueseason_site_user_league_season",
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
