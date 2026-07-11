from fastapi import APIRouter, Depends, Query

from app.core.context import Context
from app.api.deps import get_context
from app.crud.sleeper.roster import get_user_rosters, get_user_orphans
from app.schemas.commissioner import CommissionerOrphansResponse
from app.tasks.user import sync_user_data_task
from app.services.commissioner.orphans import get_commissioner_orphans
from app.services.values.basis import ValueBasis

router = APIRouter()

@router.post("/{username}/sync")
async def sync_user_data_endpoint(
    username: str,
):
    await sync_user_data_task.kiq(username)
    return {"status": "sync_initiated"}

@router.get("/{username}/rosters")
async def get_user_rosters_endpoint(
    username: str, 
    ctx: Context = Depends(get_context),
):
    return await get_user_rosters(ctx.db, ctx.sleeper, username)

@router.get("/{username}/orphans")
async def get_user_orphans_endpoint(
    username: str,
    ctx: Context = Depends(get_context),
):
    return await get_user_orphans(ctx.db, ctx.sleeper, username)


@router.get(
    "/{username}/commissioner/orphans",
    response_model=CommissionerOrphansResponse,
)
async def get_commissioner_orphans_endpoint(
    username: str,
    value_basis: ValueBasis = Query(
        ValueBasis.FANTASYCALC,
    ),
    ctx: Context = Depends(get_context),
):
    return await get_commissioner_orphans(
        db=ctx.db,
        username=username,
        value_basis=value_basis,
    )
