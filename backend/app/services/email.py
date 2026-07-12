from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings


logger = logging.getLogger(__name__)


def build_verification_link(
    token: str,
) -> str:
    return (
        f"{settings.FRONTEND_BASE_URL.rstrip('/')}"
        f"/?verify_email_token={token}"
    )


def send_email_verification_message(
    *,
    recipient: str,
    token: str,
) -> str:
    verification_link = build_verification_link(
        token,
    )

    if not settings.SMTP_HOST or not settings.EMAIL_FROM:
        logger.info(
            "Email verification link for %s: %s",
            recipient,
            verification_link,
        )
        return "log"

    message = EmailMessage()
    message["Subject"] = "Verify your Dynasty Base email"
    message["From"] = settings.EMAIL_FROM
    message["To"] = recipient
    message.set_content(
        "Verify your Dynasty Base account by opening this link:\n"
        f"{verification_link}\n\n"
        "If you did not create this account, you can ignore this email.\n"
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
