from fastapi import APIRouter, BackgroundTasks, Query

from app.api.deps import ContextDep
from app.crud.sleeper.player import sync_players
from app.schemas.player_tiers import PlayerTierBoardResponse
from app.services.values.basis import ValueBasis
from app.services.values.tiers import get_player_tier_board

router = APIRouter()

@router.post("/sync")
async def sync_players_endpoint(
    background_tasks: BackgroundTasks,
    ctx: ContextDep,
):
    background_tasks.add_task(sync_players, ctx.db, ctx.sleeper)
    return {"message": "Global player sync started"}


@router.get(
    "/tiers",
    response_model=PlayerTierBoardResponse,
)
async def get_player_tiers_endpoint(
    ctx: ContextDep,
    value_basis: ValueBasis = Query(
        ValueBasis.KTC,
    ),
    league_id: str | None = Query(
        default=None,
    ),
):
    return await get_player_tier_board(
        ctx=ctx,
        value_basis=value_basis,
        league_id=league_id,
    )
