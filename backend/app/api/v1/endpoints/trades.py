import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.api.deps import get_session
from app.crud.trade import get_trade_signals
from app.crud.leaguemate import sync_leaguemates
from app.services import sleeper

router = APIRouter()

@router.get("/{username}/trade-signals")
async def get_trade_signals_endpoint(username: str, db: Session = Depends(get_session)):
    username_details = await sleeper.get_username_details(username)
    if not username_details:
        raise HTTPException(status_code=404, detail="User not found")
    
    return await get_trade_signals(db, username_details['user_id'])

@router.post("/{username}/sync-leaguemates")
async def sync_leaguemates_endpoint(
    username: str, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session)
):
    username_details = await sleeper.get_username_details(username)
    if not username_details:
        raise HTTPException(status_code=404, detail="User not found")

    background_tasks.add_task(
        sync_leaguemates, 
        username_details['user_id'], 
        "2026"
    )
    
    return {"message": "Leaguemate sync initiated in background"}