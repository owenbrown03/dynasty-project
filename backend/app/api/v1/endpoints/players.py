from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_session
from app.crud.player import sync_players 

router = APIRouter()

@router.post("/sync")
async def sync_players_endpoint(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_session)):
    background_tasks.add_task(sync_players, db)
    return {"message": "Global player sync started"}