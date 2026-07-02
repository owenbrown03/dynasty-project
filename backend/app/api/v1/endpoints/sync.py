from fastapi import APIRouter, Depends

from app.core.context import Context
from app.api.deps import get_context

router = APIRouter()


from app.services.sleeper.projection import sync_projections

@router.post("/sleeper-projections")
async def sleeper_projections_endpoint(
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

from app.crud.ktc.sync import sync_ktc_values

@router.get("/ktc")
async def ktc_endpoint(
    ctx: Context = Depends(get_context),
):

    return await sync_ktc_values(
        db=ctx.db,
        ktc=ctx.ktc
    )


from app.crud.underdog.sync import sync_underdog_adp

@router.get("/underdog")
async def underdog_endpoint(
    ctx: Context = Depends(get_context),
):

    return await sync_underdog_adp(
        db=ctx.db,
        underdog=ctx.underdog
    )


from app.crud.fc.sync import sync_fantasycalc_values

@router.get("/fc")
async def fc_endpoint(
    ctx: Context = Depends(get_context),
):

    return await sync_fantasycalc_values(
        db=ctx.db,
        fc=ctx.fc
    )