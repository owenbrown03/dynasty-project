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
    await sync_user_data_task.kiq(body.sleeper_username)
    await sync_leaguemates_task.kiq(body.sleeper_username)
    return await upsert(ctx, sleeper_username=body.sleeper_username)

@router.post("/reconcile")
async def login_endpoint(
    ctx: ContextDep,
):
    return await reconcile(ctx)
