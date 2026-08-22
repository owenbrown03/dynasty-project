import logging
from datetime import datetime, timedelta, timezone

from app.crud.sleeper.advisor import (
    get_active_feedback_by_site_user,
    get_latest_report,
    save_report,
)
from app.schemas.advisor import AdvisorPreferenceSummary
from app.services.advisor.feedback import build_preference_summary
from app.services.advisor.synthesis import (
    synthesize_recommendations,
)

logger = logging.getLogger(__name__)

DIGEST_STALE_AFTER = timedelta(days=7)


def is_report_stale(report) -> bool:
    if report is None:
        return True

    generated_at = report.generated_at

    if generated_at.tzinfo is None:
        generated_at = generated_at.replace(
            tzinfo=timezone.utc,
        )

    return datetime.now(timezone.utc) - generated_at > DIGEST_STALE_AFTER


async def build_preferences_for_site_user(
    db,
    site_user_id,
) -> AdvisorPreferenceSummary:
    rows = await get_active_feedback_by_site_user(
        db,
        site_user_id=site_user_id,
    )

    return build_preference_summary(rows)


async def generate_and_persist_digest(
    *,
    ctx,
    username: str,
):
    from app.services.advisor.candidates import (
        build_advisor_dossier,
    )

    dossier = await build_advisor_dossier(ctx, username)

    preferences = await build_preferences_for_site_user(
        ctx.db,
        ctx.site_user.id,
    )

    synthesis = await synthesize_recommendations(
        gemini=ctx.gemini,
        redis=ctx.redis,
        dossier=dossier,
        preferences=preferences,
    )

    report = await save_report(
        ctx.db,
        site_user_id=ctx.site_user.id,
        username=username,
        payload=synthesis.model_dump(),
        model=synthesis.model or None,
    )

    return report


async def get_or_queue_digest(
    ctx,
    username: str,
) -> dict:
    if ctx.site_user is None:
        return {
            "report": None,
            "queued": False,
            "reason": "sign_in_required",
        }

    latest = await get_latest_report(
        ctx.db,
        site_user_id=ctx.site_user.id,
    )

    if not is_report_stale(latest):
        return {
            "report": latest.payload,
            "queued": False,
            "generated_at": latest.generated_at.isoformat(),
            "model": latest.model,
        }

    from app.tasks.advisor import generate_advisor_digest_task

    await generate_advisor_digest_task.kiq(username)

    logger.info(
        "Digest regeneration queued user=%s",
        username,
    )

    return {
        "report": latest.payload if latest else None,
        "queued": True,
        "generated_at": (
            latest.generated_at.isoformat()
            if latest
            else None
        ),
        "model": latest.model if latest else None,
    }
