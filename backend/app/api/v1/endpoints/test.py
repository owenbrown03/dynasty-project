from fastapi import APIRouter, Depends

from app.core.context import Context
from app.api.deps import get_context
from app.integrations.sleeper.schemas.api import Projection

from app.analytics.war.service import WARService

from app.services.sleeper.projection import sync_projections

router = APIRouter()

@router.get(
    "/projections",
    response_model=Projection,
)
async def test_projections(
    ctx: Context = Depends(get_context),
):

    projections = await ctx.sleeper.read.get_projections(
        2026
    )

    return {
        "projections": projections[:10]
    }

@router.post("/sync-projections")
async def sync_projection_endpoint(
    ctx: Context = Depends(get_context)
):

    await sync_projections(
        db=ctx.db,
        sleeper=ctx.sleeper,
        season=2026,
        force_update=True,
    )

    return {
        "status": "complete"
    }

from app.analytics.war.service import WARService


@router.get("/war")
async def test_war(
    ctx: Context = Depends(get_context),
):

    results = await WARService().calculate(
        ctx.db,
        season=2026,
    )


    return [
        {
            "name": r.name,
            "position": r.position,
            "team": r.team,
            "projection": r.projected_points,
            "replacement": r.replacement_points,
            "war": r.war,
        }
        for r in results[:50]
    ]
