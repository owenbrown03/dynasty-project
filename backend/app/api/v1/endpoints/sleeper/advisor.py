import httpx
from fastapi import APIRouter, HTTPException, Response

from app.api.deps import ContextDep
from app.schemas.advisor import (
    AdvisorFeedbackEntryListResponse,
    AdvisorFeedbackRequest,
    AdvisorFeedbackResponse,
    AdvisorPreferenceSummary,
    AdvisorInvalidateResponse,
    AdvisorSynthesisResponse,
)
from app.schemas.advisor import AdvisorDirectivesResponse
from app.services.advisor.candidates import build_advisor_dossier
from app.services.advisor.directives import build_advisor_directives
from app.services.advisor.feedback import (
    delete_feedback_entry,
    list_league_feedback,
    list_preferences,
    record_feedback,
)
from app.services.advisor.synthesis import (
    invalidate_cached_recommendations,
    peek_cached_recommendations,
    synthesize_recommendations,
)
from app.services.advisor.digest import get_or_queue_digest
from app.crud.sleeper.advisor import (
    get_active_feedback_by_site_user,
    resolve_feedback,
)
from app.services.advisor.feedback import build_preference_summary

router = APIRouter()


def _dossier_league_ids(dossier) -> list[str]:
    ids = [
        rc.league_id
        for rc in dossier.roster_contexts
        if rc.league_id
    ]
    if dossier.scope_league_id:
        return [dossier.scope_league_id]
    return ids


async def _load_preferences(
    ctx: ContextDep,
    dossier=None,
):
    if ctx.site_user is None or ctx.db is None:
        return None

    rows = await get_active_feedback_by_site_user(
        ctx.db,
        site_user_id=ctx.site_user.id,
        league_ids=(
            _dossier_league_ids(dossier)
            if dossier is not None
            else None
        ),
    )

    if not rows:
        return None

    return build_preference_summary(rows)


@router.get(
    "/{username}/directives",
    response_model=AdvisorDirectivesResponse,
)
async def get_advisor_directives_endpoint(
    username: str,
    ctx: ContextDep,
    league_id: str | None = None,
) -> AdvisorDirectivesResponse:
    """Deterministic roster directives (over-limit alerts).

    No AI generation and no quota; reads normalized data only.
    """
    if ctx.connection is None:
        raise HTTPException(
            status_code=401,
            detail=(
                "Link a Sleeper account to check roster directives."
            ),
        )

    return await build_advisor_directives(
        ctx,
        username,
        league_id=league_id,
    )


@router.post(
    "/{username}/recommendations",
    response_model=AdvisorSynthesisResponse,
)
async def get_advisor_recommendations_endpoint(
    username: str,
    ctx: ContextDep,
    league_id: str | None = None,
    force: bool = False,
) -> AdvisorSynthesisResponse:
    if ctx.site_user is None or ctx.connection is None:
        raise HTTPException(
            status_code=401,
            detail=(
                "Sign in with a linked Sleeper account to generate "
                "AI trade recommendations."
            ),
        )

    dossier = await build_advisor_dossier(
        ctx,
        username,
        league_id=league_id,
        force=force,
    )
    preferences = await _load_preferences(ctx, dossier)

    try:
        return await synthesize_recommendations(
            gemini=ctx.gemini,
            redis=ctx.redis,
            dossier=dossier,
            preferences=preferences,
            force=force,
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            detail = (
                "Gemini is rate limiting requests right now (free tier). "
                "Please try again in a minute."
            )
        else:
            detail = (
                "AI advisor upstream is temporarily unavailable. "
                "Please try again shortly."
            )

        raise HTTPException(
            status_code=503,
            detail=detail,
        ) from exc


@router.get(
    "/{username}/recommendations",
    response_model=AdvisorSynthesisResponse | None,
)
async def peek_advisor_recommendations_endpoint(
    username: str,
    ctx: ContextDep,
    league_id: str | None = None,
) -> AdvisorSynthesisResponse | Response:
    """Returns the cached recommendations for this scope, or 204 if none.

    Never triggers generation and never consumes Gemini quota.
    """
    if ctx.site_user is None or ctx.connection is None:
        raise HTTPException(
            status_code=401,
            detail=(
                "Sign in with a linked Sleeper account to view "
                "AI trade recommendations."
            ),
        )

    dossier = await build_advisor_dossier(
        ctx,
        username,
        league_id=league_id,
    )
    preferences = await _load_preferences(ctx, dossier)

    cached = await peek_cached_recommendations(
        gemini=ctx.gemini,
        redis=ctx.redis,
        dossier=dossier,
        preferences=preferences,
    )

    if cached is None:
        return Response(status_code=204)

    return cached


@router.post("/feedback", response_model=AdvisorFeedbackResponse)
async def record_advisor_feedback_endpoint(
    ctx: ContextDep,
    body: AdvisorFeedbackRequest,
) -> AdvisorFeedbackResponse:
    return await record_feedback(ctx, body)


@router.post("/feedback/{feedback_id}/resolve")
async def resolve_advisor_feedback_endpoint(
    feedback_id: int,
    ctx: ContextDep,
) -> dict:
    if ctx.site_user is None:
        raise HTTPException(
            status_code=401,
            detail="Sign in before resolving advisor feedback.",
        )

    resolved = await resolve_feedback(
        ctx.db,
        site_user_id=ctx.site_user.id,
        feedback_id=feedback_id,
    )

    if not resolved:
        raise HTTPException(
            status_code=404,
            detail="Feedback not found.",
        )

    return {"id": feedback_id, "resolved": True}


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


@router.get("/feedback", response_model=AdvisorFeedbackEntryListResponse)
async def list_advisor_feedback_endpoint(
    ctx: ContextDep,
    league_id: str = "",
) -> AdvisorFeedbackEntryListResponse:
    if ctx.site_user is None:
        raise HTTPException(
            status_code=401,
            detail="Sign in before viewing advisor feedback.",
        )

    if not league_id:
        raise HTTPException(
            status_code=422,
            detail="league_id is required.",
        )

    return await list_league_feedback(ctx, league_id)


@router.delete("/feedback/{feedback_id}")
async def delete_advisor_feedback_endpoint(
    feedback_id: int,
    ctx: ContextDep,
) -> dict:
    if ctx.site_user is None:
        raise HTTPException(
            status_code=401,
            detail="Sign in before deleting advisor feedback.",
        )

    await delete_feedback_entry(ctx, feedback_id)

    return {"id": feedback_id, "deleted": True}


@router.post(
    "/{username}/invalidate",
    response_model=AdvisorInvalidateResponse,
)
async def invalidate_advisor_recommendations_endpoint(
    username: str,
    ctx: ContextDep,
    league_id: str | None = None,
) -> AdvisorInvalidateResponse:
    if ctx.site_user is None:
        raise HTTPException(
            status_code=401,
            detail="Sign in before clearing cached recommendations.",
        )

    preferences = await _load_preferences(ctx)

    invalidated = await invalidate_cached_recommendations(
        redis=ctx.redis,
        username=username,
        league_id=league_id,
        preferences=preferences,
    )

    return AdvisorInvalidateResponse(invalidated=invalidated)

