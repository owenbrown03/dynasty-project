from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.sleeper.client import SleeperClient
from app.tasks.trade import sync_leaguemates_task
from app.api.deps import get_db, get_user_sleeper_client
from app.crud.sleeper.trade import get_trade_signals

router = APIRouter()

@router.get("/{username}/trade-signals")
async def get_trade_signals_endpoint(
    username: str,
    sleeper: SleeperClient = Depends(get_user_sleeper_client),
    db: AsyncSession = Depends(get_db),
):
    return await get_trade_signals(db, username, sleeper)

@router.post("/{username}/sync-leaguemates")
async def sync_leaguemates_endpoint(
    username: str,
):
    await sync_leaguemates_task.kiq(username)
    return {
        "status": "queued",
        "message": "Leaguemate sync added to queue",
        "username": username,
    }