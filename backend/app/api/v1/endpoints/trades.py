from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.crud.trade import trade_signals
from app.crud.leaguemate import leaguemate_sync

from app.services import sleeper

router = APIRouter()

@router.get("/{username}")
async def get_trade_signals(username: str, db: Session = Depends(get_db)):
    user_data = await sleeper.get_username_details(username)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    return await trade_signals(db, user_data['user_id'])

@router.post("/{username}/sync-leaguemates")
async def sync_leaguemates(
    username: str, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):

    user_data = await sleeper.get_username_details(username)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    background_tasks.add_task(
        leaguemate_sync, 
        db, 
        user_data['user_id'], 
        "2026" #TODO: season should be dynamic
    )
    
    return {"message": "Leaguemate sync initiated in background"}