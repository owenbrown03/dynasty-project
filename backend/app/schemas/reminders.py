from datetime import datetime

from pydantic import Field

from app.schemas.base import Base


class ReminderItem(Base):
    id: int
    league_id: str | None = None
    title: str
    note: str = ""
    due_week: int | None = None
    due_season: str | None = None
    delivery_channel: str = "in_app"
    completed: bool = False
    email_sent_at: datetime | None = None
    updated_at: datetime


class ReminderListResponse(Base):
    reminders: list[ReminderItem] = Field(
        default_factory=list,
    )


class ReminderCreate(Base):
    league_id: str | None = None
    title: str
    note: str = ""
    due_week: int | None = None
    due_season: str | None = None
    delivery_channel: str = "in_app"


class ReminderUpdate(Base):
    id: int
    title: str
    note: str = ""
    due_week: int | None = None
    due_season: str | None = None
    delivery_channel: str = "in_app"
    completed: bool = False
