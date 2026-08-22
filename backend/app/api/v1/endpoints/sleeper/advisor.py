from fastapi import APIRouter

from app.api.deps import ContextDep
from app.schemas.advisor import AdvisorSynthesisResponse
from app.services.advisor.candidates import build_advisor_dossier
from app.services.advisor.synthesis import (
    synthesize_recommendations,
)

router = APIRouter()


@router.post(
    "/{username}/recommendations",
    response_model=AdvisorSynthesisResponse,
)
async def get_advisor_recommendations_endpoint(
    username: str,
    ctx: ContextDep,
) -> AdvisorSynthesisResponse:
    dossier = await build_advisor_dossier(ctx, username)

    return await synthesize_recommendations(
        gemini=ctx.gemini,
        redis=ctx.redis,
        dossier=dossier,
    )
