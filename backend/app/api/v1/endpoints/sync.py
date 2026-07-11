from fastapi import APIRouter

from app.api.deps import ContextDep
from app.crud.fc.sync import sync_fantasycalc_values
from app.crud.ktc.sync import sync_ktc_values
from app.crud.underdog.sync import sync_underdog_adp
from app.services.sleeper.projection import sync_projections

router = APIRouter()

@router.post("/sleeper-projections")
async def sleeper_projections_endpoint(
    ctx: ContextDep,
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

@router.get("/ktc")
async def ktc_endpoint(
    ctx: ContextDep,
):
    return await sync_ktc_values(
        db=ctx.db,
        ktc=ctx.ktc
    )

@router.get("/underdog")
async def underdog_endpoint(
    ctx: ContextDep,
):
    return await sync_underdog_adp(
        db=ctx.db,
        underdog=ctx.underdog
    )

@router.get("/fc")
async def fc_endpoint(
    ctx: ContextDep,
):
    return await sync_fantasycalc_values(
        db=ctx.db,
        fc=ctx.fc
    )
