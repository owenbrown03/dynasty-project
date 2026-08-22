import logging

from fastapi import HTTPException

from app.api.deps import ContextDep
from app.crud.sleeper.advisor import (
    create_feedback,
    get_active_feedback_by_site_user,
)
from app.schemas.advisor import (
    ACTION_GITHUB_ISSUE,
    ACTION_VALUES_DOWNGRADE,
    ALLOWED_FEEDBACK_SENTIMENTS,
    ALLOWED_FEEDBACK_TAGS,
    AdvisorFeedbackRequest,
    AdvisorFeedbackResponse,
    AdvisorPreferenceSummary,
)

logger = logging.getLogger(__name__)

MAX_REASON_LENGTH = 1000
MAX_TAGS = 8
MAX_PLAYER_IDS = 30


def _require_site_user(ctx: ContextDep):
    if ctx.site_user is None:
        raise HTTPException(
            status_code=401,
            detail=(
                "Sign in before recording advisor feedback."
            ),
        )

    return ctx.site_user


def validate_feedback_request(
    request: AdvisorFeedbackRequest,
) -> None:
    if request.sentiment not in ALLOWED_FEEDBACK_SENTIMENTS:
        raise HTTPException(
            status_code=422,
            detail=(
                "sentiment must be one of: "
                f"{sorted(ALLOWED_FEEDBACK_SENTIMENTS)}"
            ),
        )

    invalid_tags = [
        tag
        for tag in request.tags
        if tag not in ALLOWED_FEEDBACK_TAGS
    ]

    if invalid_tags:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown feedback tags: {invalid_tags}",
        )

    if request.reason and len(request.reason) > MAX_REASON_LENGTH:
        raise HTTPException(
            status_code=422,
            detail=(
                "reason is too long "
                f"(max {MAX_REASON_LENGTH} characters)"
            ),
        )

    if len(request.tags) > MAX_TAGS:
        raise HTTPException(
            status_code=422,
            detail=f"Too many tags (max {MAX_TAGS})",
        )

    if len(request.player_ids) > MAX_PLAYER_IDS:
        raise HTTPException(
            status_code=422,
            detail=f"Too many player ids (max {MAX_PLAYER_IDS})",
        )


async def record_feedback(
    ctx: ContextDep,
    request: AdvisorFeedbackRequest,
) -> AdvisorFeedbackResponse:
    site_user = _require_site_user(ctx)
    validate_feedback_request(request)

    allowed_actions = {
        ACTION_VALUES_DOWNGRADE,
        ACTION_GITHUB_ISSUE,
    }

    action_taken = request.action_taken

    if action_taken is not None and action_taken not in allowed_actions:
        logger.warning(
            "Unknown advisor feedback action %s",
            action_taken,
        )
        action_taken = None

    feedback = await create_feedback(
        ctx.db,
        site_user_id=site_user.id,
        league_id=request.league_id,
        counterparty_id=request.counterparty_id,
        player_ids=request.player_ids,
        sentiment=request.sentiment,
        reason=request.reason,
        tags=request.tags,
        proposal_snapshot=request.proposal_snapshot,
        action_taken=action_taken,
    )

    return AdvisorFeedbackResponse(
        id=feedback.id,
        sentiment=feedback.sentiment,
        reason=feedback.reason,
        tags=feedback.tags,
        resolved=feedback.resolved,
        created_at=feedback.created_at.isoformat(),
    )


async def list_preferences(
    ctx: ContextDep,
) -> AdvisorPreferenceSummary:
    site_user = _require_site_user(ctx)

    rows = await get_active_feedback_by_site_user(
        ctx.db,
        site_user_id=site_user.id,
    )

    return build_preference_summary(rows)


def build_preference_summary(
    rows,
) -> AdvisorPreferenceSummary:
    summary = AdvisorPreferenceSummary()

    for row in rows:
        if row.action_taken == ACTION_VALUES_DOWNGRADE:
            continue

        note_parts = [row.reason] if row.reason else []

        if row.tags:
            note_parts.append(f"tags: {', '.join(row.tags)}")

        if not note_parts:
            continue

        target_list = (
            summary.likes
            if row.sentiment == "like"
            else summary.dislikes
        )

        target_list.append("; ".join(note_parts))

        for tag in row.tags:
            summary.tags[tag] = summary.tags.get(tag, 0) + 1

    return summary
