from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.crud import player

router = APIRouter()

@router.post("/sync")
async def sync_players(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    background_tasks.add_task(player.sync_players, db)
    return {"message": "Global player sync started"}