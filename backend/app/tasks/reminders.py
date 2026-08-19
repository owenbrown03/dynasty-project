import logging
from datetime import datetime

from app.core.broker import broker
from app.core.database import AsyncSessionLocal
from app.crud.auth.user import is_email_verified
from app.crud.sleeper.personal import (
    get_reminders_by_user,
    mark_reminder_email_sent,
)
from app.infrastructure.redis.manager import RedisManager
from app.models.db.auth import SiteUser
from app.services.email import send_reminder_email_message
from sqlmodel import select

logger = logging.getLogger(__name__)

REMINDERS_LOCK_KEY = "sync:reminders:lock"
REMINDERS_LOCK_TTL_SECONDS = 300


async def acquire_reminders_lock() -> str | None:
    redis = await RedisManager.get()
    import uuid

    token = uuid.uuid4().hex

    acquired = await redis.set(
        REMINDERS_LOCK_KEY,
        token,
        ex=REMINDERS_LOCK_TTL_SECONDS,
        nx=True,
    )

    if acquired:
        return token

    return None


async def release_reminders_lock(token: str) -> None:
    redis = await RedisManager.get()
    current = await redis.get(REMINDERS_LOCK_KEY)

    if current == token:
        await redis.delete(REMINDERS_LOCK_KEY)


@broker.task
async def send_due_reminder_emails_task():
    lock_token = await acquire_reminders_lock()

    if lock_token is None:
        logger.info(
            "Skipping reminder emails; another instance is running",
        )
        return {"status": "skipped", "reason": "already_running"}

    try:
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
    finally:
        await release_reminders_lock(lock_token)
