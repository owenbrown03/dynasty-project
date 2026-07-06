from fastapi import APIRouter, Depends

from app.core.context import Context
from app.api.deps import get_context
from app.tasks.trade import sync_leaguemates_task
from app.crud.sleeper.trade import get_trade_signals

router = APIRouter()

@router.get("/{username}/trade-signals")
async def get_trade_signals_endpoint(
    username: str,
    ctx: Context = Depends(get_context),
):
    return await get_trade_signals(ctx.db, ctx.sleeper, username)

@router.post("/{username}/sync-leaguemates")
async def sync_leaguemates_endpoint(username: str):
    await sync_leaguemates_task.kiq(username)
    return {
        "status": "queued",
        "message": "Leaguemate sync added to queue",
        "username": username,
    }