import httpx
from fastapi import APIRouter, HTTPException

from app.api.deps import ContextDep
from app.schemas.advisor import (
    AdvisorFeedbackRequest,
    AdvisorFeedbackResponse,
    AdvisorPreferenceSummary,
    AdvisorSynthesisResponse,
)
from app.services.advisor.candidates import build_advisor_dossier
from app.services.advisor.feedback import (
    list_preferences,
    record_feedback,
)
from app.services.advisor.synthesis import (
    synthesize_recommendations,
)
from app.services.advisor.digest import get_or_queue_digest
from app.crud.sleeper.advisor import get_active_feedback_by_site_user
from app.services.advisor.feedback import build_preference_summary

router = APIRouter()


async def _load_preferences(ctx: ContextDep):
    if ctx.site_user is None or ctx.db is None:
        return None

    rows = await get_active_feedback_by_site_user(
        ctx.db,
        site_user_id=ctx.site_user.id,
    )

    if not rows:
        return None

    return build_preference_summary(rows)


@router.post(
    "/{username}/recommendations",
    response_model=AdvisorSynthesisResponse,
)
async def get_advisor_recommendations_endpoint(
    username: str,
    ctx: ContextDep,
) -> AdvisorSynthesisResponse:
    if ctx.site_user is None or ctx.connection is None:
        raise HTTPException(
            status_code=401,
            detail=(
                "Sign in with a linked Sleeper account to generate "
                "AI trade recommendations."
            ),
        )

    dossier = await build_advisor_dossier(ctx, username)
    preferences = await _load_preferences(ctx)

    try:
        return await synthesize_recommendations(
            gemini=ctx.gemini,
            redis=ctx.redis,
            dossier=dossier,
            preferences=preferences,
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "AI advisor upstream is temporarily unavailable. "
                "Please try again shortly."
            ),
        ) from exc


@router.post("/feedback", response_model=AdvisorFeedbackResponse)
async def record_advisor_feedback_endpoint(
    ctx: ContextDep,
    body: AdvisorFeedbackRequest,
) -> AdvisorFeedbackResponse:
    return await record_feedback(ctx, body)


@router.get("/preferences", response_model=AdvisorPreferenceSummary)
async def get_advisor_preferences_endpoint(
    ctx: ContextDep,
) -> AdvisorPreferenceSummary:
    return await list_preferences(ctx)


@router.get("/{username}/digest")
async def get_advisor_digest_endpoint(
    username: str,
    ctx: ContextDep,
):
    return await get_or_queue_digest(ctx, username)
