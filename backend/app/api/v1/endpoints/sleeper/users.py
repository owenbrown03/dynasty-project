from fastapi import APIRouter, Depends

from app.core.context import Context
from app.api.deps import get_context
from app.crud.sleeper.roster import get_user_rosters, get_user_orphans
from app.tasks.user import sync_user_data_task

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