from fastapi import APIRouter, Depends

from app.integrations.sleeper import types
from app.core.context import Context
from app.api.deps import get_context
from app.services.sleeper.connection import upsert
from app.tasks.user import sync_user_data_task
from app.tasks.trade import sync_leaguemates_task
from app.crud.sleeper.connection import reconcile

router = APIRouter()

@router.post('/upsert')
async def upsert_endpoint(
    body: types.UpsertSleeperRequest,
    ctx: Context = Depends(get_context)
):

    await sync_user_data_task.kiq(body.sleeper_username)
    await sync_leaguemates_task.kiq(body.sleeper_username)
    return await upsert(ctx, sleeper_username=body.sleeper_username)

    # job_id = generate_job_id()

    # sync_user_data_task.kiq(body.sleeper_username, job_id)
    # sync_leaguemates_task.kiq(body.sleeper_username, job_id)

    # return {
    # "connection": conn,
    # "sync_job_id": job_id,
    # }

@router.post("/reconcile")
async def login_endpoint(
    ctx: Context = Depends(get_context),
):
    return await reconcile(ctx)