from __future__ import annotations

from fastapi import HTTPException, status

from app.core.context import Context
from app.crud.sleeper.personal import (
    get_reminder_by_id,
    get_reminders_by_user,
    insert_reminder,
    update_reminder,
)
from app.schemas.reminders import (
    ReminderCreate,
    ReminderItem,
    ReminderListResponse,
    ReminderUpdate,
)


def _require_reminder_context(
    ctx: Context,
) -> None:
    if ctx.site_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )


def to_reminder_item(
    reminder,
) -> ReminderItem:
    return ReminderItem(
        id=reminder.id,
        league_id=reminder.league_id,
        title=reminder.title,
        note=reminder.note,
        due_week=reminder.due_week,
        due_season=reminder.due_season,
        delivery_channel=reminder.delivery_channel,
        completed=reminder.completed,
        email_sent_at=reminder.email_sent_at,
        updated_at=reminder.updated_at,
    )


async def list_reminders(
    ctx: Context,
) -> ReminderListResponse:
    _require_reminder_context(
        ctx,
    )

    reminders = await get_reminders_by_user(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
    )

    return ReminderListResponse(
        reminders=[
            to_reminder_item(reminder)
            for reminder in reminders
        ],
    )


async def create_reminder(
    body: ReminderCreate,
    ctx: Context,
) -> ReminderItem:
    _require_reminder_context(
        ctx,
    )

    reminder = await insert_reminder(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
        league_id=body.league_id,
        title=body.title,
        note=body.note,
        due_week=body.due_week,
        due_season=body.due_season,
        delivery_channel=body.delivery_channel,
    )

    return to_reminder_item(
        reminder,
    )


async def save_reminder(
    body: ReminderUpdate,
    ctx: Context,
) -> ReminderItem:
    _require_reminder_context(
        ctx,
    )

    reminder = await get_reminder_by_id(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
        reminder_id=body.id,
    )

    if reminder is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found",
        )

    updated = await update_reminder(
        db=ctx.db,
        reminder=reminder,
        title=body.title,
        note=body.note,
        due_week=body.due_week,
        due_season=body.due_season,
        delivery_channel=body.delivery_channel,
        completed=body.completed,
    )

    return to_reminder_item(
        updated,
    )
