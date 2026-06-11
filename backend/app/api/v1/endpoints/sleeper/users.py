from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.sleeper.client import SleeperClient
from app.api.deps import get_db, get_user_sleeper_client
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
    sleeper: SleeperClient = Depends(get_user_sleeper_client),
    db: AsyncSession = Depends(get_db)
):
    return await get_user_rosters(db, sleeper, username)

@router.get("/{username}/orphans")
async def get_user_orphans_endpoint(
    username: str,
    sleeper: SleeperClient = Depends(get_user_sleeper_client),
    db: AsyncSession = Depends(get_db)
):
    return await get_user_orphans(db, sleeper, username)