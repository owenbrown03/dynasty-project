from fastapi import APIRouter

from app.api.deps import ContextDep
from app.integrations.sleeper import types
from app.crud.sleeper.connection import reconcile
from app.services.sleeper.connection import upsert
from app.tasks.trade import sync_leaguemates_task
from app.tasks.user import sync_user_data_task

router = APIRouter()

@router.post('/upsert')
async def upsert_endpoint(
    body: types.UpsertSleeperRequest,
    ctx: ContextDep,
):
    if ctx.redis is not None:
        from app.services.dashboard.service import build_dashboard_cache_prefix
        from app.services.leagues.details import build_league_details_cache_prefix
        await ctx.redis.delete_prefix(build_dashboard_cache_prefix())
        await ctx.redis.delete_prefix(build_league_details_cache_prefix())

    await sync_user_data_task.kiq(body.sleeper_username)
    await sync_leaguemates_task.kiq(body.sleeper_username, force=True)
    return await upsert(ctx, sleeper_username=body.sleeper_username)

@router.post("/reconcile")
async def login_endpoint(
    ctx: ContextDep,
):
    return await reconcile(ctx)
