from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.api.deps import get_session
from app.crud.player import sync_players 

router = APIRouter()

@router.post("/sync")
async def sync_players_endpoint(background_tasks: BackgroundTasks, db: Session = Depends(get_session)):
    background_tasks.add_task(sync_players, db)
    return {"message": "Global player sync started"}