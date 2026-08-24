from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.db.sleeper.personal import (
    AdvisorFeedback,
    AdvisorReport,
)

# Feedback older than this is treated as resolved at query time so a
# stale dislike from months ago cannot keep steering recommendations.
FEEDBACK_ACTIVE_TTL_DAYS = 180


async def create_feedback(
    db: AsyncSession,
    *,
    site_user_id,
    league_id: str | None,
    counterparty_id: str | None,
    player_ids: list[str],
    sentiment: str,
    reason: str | None,
    tags: list[str],
    proposal_snapshot: dict,
    action_taken: str | None,
) -> AdvisorFeedback:
    feedback = AdvisorFeedback(
        site_user_id=site_user_id,
        league_id=league_id,
        counterparty_id=counterparty_id,
        player_ids=player_ids,
        sentiment=sentiment,
        reason=reason,
        tags=tags,
        proposal_snapshot=proposal_snapshot,
        action_taken=action_taken,
    )

    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)

    return feedback


async def get_active_feedback_by_site_user(
    db: AsyncSession,
    *,
    site_user_id,
    league_ids: list[str] | None = None,
    active_within_days: int | None = FEEDBACK_ACTIVE_TTL_DAYS,
) -> list[AdvisorFeedback]:
    """Active (unresolved, unexpired) feedback for a user.

    When ``league_ids`` is provided, only feedback recorded in those
    leagues is returned so memory earned in one league does not bleed
    into another. Rows older than the TTL window are treated as
    resolved at query time.
    """
    query = select(AdvisorFeedback).where(
        AdvisorFeedback.site_user_id == site_user_id,
        AdvisorFeedback.resolved == False,  # noqa: E712
    )

    if league_ids is not None:
        query = query.where(
            AdvisorFeedback.league_id.in_(league_ids),
        )

    if active_within_days is not None:
        cutoff = datetime.utcnow() - timedelta(
            days=active_within_days,
        )
        query = query.where(AdvisorFeedback.created_at >= cutoff)

    result = await db.execute(
        query.order_by(AdvisorFeedback.created_at.desc()).limit(50),
    )
    return list(result.scalars().all())


async def resolve_feedback(
    db: AsyncSession,
    *,
    site_user_id,
    feedback_id: int,
) -> bool:
    feedback = (
        await db.execute(
            select(AdvisorFeedback).where(
                AdvisorFeedback.id == feedback_id,
                AdvisorFeedback.site_user_id == site_user_id,
            )
        )
    ).scalar_one_or_none()

    if feedback is None:
        return False

    feedback.resolved = True
    await db.commit()

    return True


async def save_report(
    db: AsyncSession,
    *,
    site_user_id,
    username: str,
    payload: dict,
    model: str | None,
) -> AdvisorReport:
    report = AdvisorReport(
        site_user_id=site_user_id,
        username=username,
        payload=payload,
        model=model,
    )

    db.add(report)
    await db.commit()
    await db.refresh(report)

    return report


async def get_latest_report(
    db: AsyncSession,
    *,
    site_user_id,
) -> AdvisorReport | None:
    result = await db.execute(
        select(AdvisorReport)
        .where(AdvisorReport.site_user_id == site_user_id)
        .order_by(AdvisorReport.generated_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_site_user_connection_by_sleeper_user_id(
    db: AsyncSession,
    *,
    sleeper_user_id: str,
):
    from app.models.db.auth import SiteUser
    from app.models.db.sleeper.connection import (
        SleeperConnection,
    )

    result = await db.execute(
        select(SiteUser, SleeperConnection)
        .join(
            SleeperConnection,
            SleeperConnection.site_user_id == SiteUser.id,
        )
        .where(
            SleeperConnection.sleeper_user_id
            == sleeper_user_id
        )
        .limit(1)
    )
    return result.first()


async def list_active_feedback_for_league(
    db: AsyncSession,
    *,
    site_user_id,
    league_id: str,
) -> list[AdvisorFeedback]:
    result = await db.execute(
        select(AdvisorFeedback)
        .where(
            AdvisorFeedback.site_user_id == site_user_id,
            AdvisorFeedback.league_id == league_id,
            AdvisorFeedback.resolved == False,  # noqa: E712
        )
        .order_by(AdvisorFeedback.created_at.desc()),
    )
    return list(result.scalars().all())


async def delete_feedback(
    db: AsyncSession,
    *,
    site_user_id,
    feedback_id: int,
) -> bool:
    feedback = (
        await db.execute(
            select(AdvisorFeedback).where(
                AdvisorFeedback.id == feedback_id,
                AdvisorFeedback.site_user_id == site_user_id,
            )
        )
    ).scalar_one_or_none()

    if feedback is None:
        return False

    await db.delete(feedback)
    await db.commit()
    return True
