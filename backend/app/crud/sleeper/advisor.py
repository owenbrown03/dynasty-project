from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.db.sleeper.personal import AdvisorFeedback


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
    limit: int = 50,
) -> list[AdvisorFeedback]:
    result = await db.execute(
        select(AdvisorFeedback)
        .where(
            AdvisorFeedback.site_user_id == site_user_id,
            AdvisorFeedback.resolved == False,  # noqa: E712
        )
        .order_by(AdvisorFeedback.created_at.desc())
        .limit(limit)
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
