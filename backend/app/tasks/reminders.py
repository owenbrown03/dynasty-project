from datetime import datetime

from app.core.broker import broker
from app.core.database import AsyncSessionLocal
from app.crud.auth.user import is_email_verified
from app.crud.sleeper.personal import (
    get_reminders_by_user,
    mark_reminder_email_sent,
)
from app.models.db.auth import SiteUser
from app.services.email import send_reminder_email_message
from sqlmodel import select


@broker.task
async def send_due_reminder_emails_task():
    async with AsyncSessionLocal() as db:
        users = (
            await db.execute(
                select(SiteUser)
            )
        ).scalars().all()

        current_year = str(datetime.now().year)

        for user in users:
            if not is_email_verified(user):
                continue

            reminders = await get_reminders_by_user(
                db=db,
                site_user_id=user.id,
            )

            for reminder in reminders:
                if reminder.completed:
                    continue

                if reminder.delivery_channel != "email":
                    continue

                if reminder.email_sent_at is not None:
                    continue

                if reminder.due_season not in {None, current_year}:
                    continue

                send_reminder_email_message(
                    recipient=user.email,
                    title=reminder.title,
                    note=reminder.note,
                    league_id=reminder.league_id,
                    due_season=reminder.due_season,
                    due_week=reminder.due_week,
                )

                await mark_reminder_email_sent(
                    db=db,
                    reminder=reminder,
                )
