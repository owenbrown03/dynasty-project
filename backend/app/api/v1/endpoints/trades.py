from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.tasks.trade import sync_leaguemates_task
from app.api.deps import get_session
from app.crud.trade import get_trade_signals

router = APIRouter()

@router.get("/{username}/trade-signals")
async def get_trade_signals_endpoint(username: str, db: AsyncSession = Depends(get_session)):
    return await get_trade_signals(db, username)

@router.post("/{username}/sync-leaguemates")
async def sync_leaguemates_endpoint(username: str):
    await sync_leaguemates_task.kiq(username=username)
    return {
        "status": "queued", 
        "message": "Leaguemate sync added to queue",
        "username": username
    }