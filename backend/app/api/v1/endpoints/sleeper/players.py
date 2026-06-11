from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.sleeper.client import SleeperClient
from app.api.deps import get_db, get_user_sleeper_client
from app.crud.sleeper.player import sync_players

router = APIRouter()

@router.post("/sync")
async def sync_players_endpoint(
    background_tasks: BackgroundTasks,
    sleeper: SleeperClient = Depends(get_user_sleeper_client),
    db: AsyncSession = Depends(get_db)
):
    background_tasks.add_task(sync_players, db, sleeper)
    return {"message": "Global player sync started"}