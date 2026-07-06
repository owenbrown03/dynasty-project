from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import Context
from app.api.deps import get_context
from app.crud.sleeper.player import sync_players

router = APIRouter()

@router.post("/sync")
async def sync_players_endpoint(
    background_tasks: BackgroundTasks,
    ctx: Context = Depends(get_context),
):
    background_tasks.add_task(sync_players, ctx.db, ctx.sleeper)
    return {"message": "Global player sync started"}