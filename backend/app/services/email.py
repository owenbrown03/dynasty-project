from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings


logger = logging.getLogger(__name__)


def build_verification_link(
    token: str,
) -> str:
    frontend_base_url = (
        settings.FRONTEND_BASE_URL.strip()
        if settings.FRONTEND_BASE_URL
        else ""
    ) or "http://localhost:5173"
    return (
        f"{frontend_base_url.rstrip('/')}"
        f"/?verify_email_token={token}"
    )


def send_email_verification_message(
    *,
    recipient: str,
    token: str,
) -> tuple[str, str]:
    verification_link = build_verification_link(
        token,
    )

    if not settings.SMTP_HOST or not settings.EMAIL_FROM:
        logger.info(
            "Email verification link for %s: %s",
            recipient,
            verification_link,
        )
        return "log", verification_link

    message = EmailMessage()
    message["Subject"] = "Verify your Dynasty Base email"
    message["From"] = settings.EMAIL_FROM
    message["To"] = recipient
    message.set_content(
        "Verify your Dynasty Base account by opening this link:\n"
        f"{verification_link}\n\n"
        "If you did not create this account, you can ignore this email.\n"
    )

    try:
        with smtplib.SMTP(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            timeout=10,
        ) as smtp:
            if settings.SMTP_USE_TLS:
                smtp.starttls()

            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                smtp.login(
                    settings.SMTP_USERNAME,
                    settings.SMTP_PASSWORD,
                )

            smtp.send_message(message)
    except (OSError, smtplib.SMTPException):
        logger.exception(
            "SMTP email verification failed for %s. Falling back to logged link.",
            recipient,
        )
        logger.info(
            "Email verification link for %s: %s",
            recipient,
            verification_link,
        )
        return "log", verification_link

    return "smtp", verification_link


def send_reminder_email_message(
    *,
    recipient: str,
    title: str,
    note: str,
    league_id: str | None,
    due_season: str | None,
    due_week: int | None,
) -> str:
    if not settings.SMTP_HOST or not settings.EMAIL_FROM:
        logger.info(
            "Reminder email for %s: %s | league=%s season=%s week=%s | %s",
            recipient,
            title,
            league_id,
            due_season,
            due_week,
            note,
        )
        return "log"

    message = EmailMessage()
    message["Subject"] = f"Dynasty Base reminder: {title}"
    message["From"] = settings.EMAIL_FROM
    message["To"] = recipient
    message.set_content(
        f"{title}\n\n"
        f"{note}\n\n"
        f"League: {league_id or 'General'}\n"
        f"Season: {due_season or 'Any'}\n"
        f"Week: {due_week or 'Any'}\n"
    )

    with smtplib.SMTP(
        settings.SMTP_HOST,
        settings.SMTP_PORT,
        timeout=10,
    ) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()

        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            smtp.login(
                settings.SMTP_USERNAME,
                settings.SMTP_PASSWORD,
            )

        smtp.send_message(message)

    return "smtp"
