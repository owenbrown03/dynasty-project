from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.crud.roster import get_user_rosters, get_user_orphans
from app.tasks.user import sync_user_data_task

router = APIRouter()

@router.post("/{username}/sync")
async def sync_user_data_endpoint(username: str):    
    await sync_user_data_task.kiq(username=username)
    return {
        "status": "sync_initiated", 
        "message": "User historical data sync sent to background workers."
    }

@router.get("/{username}/rosters")
async def get_user_rosters_endpoint(username: str, db: AsyncSession = Depends(get_session)):
    return await get_user_rosters(db, username)

@router.get("/{username}/orphans")
async def get_user_orphans_endpoint(username, db: AsyncSession = Depends(get_session)):
    return await get_user_orphans(db, username)