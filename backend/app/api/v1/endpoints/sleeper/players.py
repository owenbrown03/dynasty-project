import logging
import time

from fastapi import APIRouter, BackgroundTasks, Query, Request

from app.api.cancellation import cancel_on_disconnect
from app.api.deps import ContextDep
from app.crud.sleeper.player import sync_players
from app.schemas.player_tiers import PlayerTierBoardResponse
from app.services.values.basis import ValueBasis
from app.services.values.tiers import get_player_tier_board

router = APIRouter()
log = logging.getLogger(__name__)

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
    request: Request,
    ctx: ContextDep,
    value_basis: ValueBasis = Query(
        ValueBasis.KTC,
    ),
    league_id: str | None = Query(
        default=None,
    ),
    cheap: bool = False,
):
    t0 = time.monotonic()
    log.info(
        "TIER_REQUEST_START basis=%s league=%s has_connection=%s user=%s cheap=%s",
        value_basis,
        league_id,
        ctx.connection is not None,
        ctx.site_user.id if ctx.site_user else None,
        cheap,
    )
    try:
        async with cancel_on_disconnect(request):
            result = await get_player_tier_board(
                ctx=ctx,
                value_basis=value_basis,
                league_id=league_id,
                cheap=cheap,
            )
            log.info(
                "TIER_REQUEST_OK basis=%s league=%s elapsed=%.2fs",
                value_basis,
                league_id,
                time.monotonic() - t0,
            )
            return result
    except Exception as exc:
        log.info(
            "TIER_REQUEST_ERR basis=%s league=%s elapsed=%s err=%s",
            value_basis,
            league_id,
            f"{time.monotonic() - t0:.2f}s",
            exc,
        )
        raise
