from fastapi import (
    APIRouter,
    HTTPException,
    status,
    Depends,
    Query,
)

from app.core.context import Context
from app.api.deps import get_context
from app.tasks.trade import sync_leaguemates_task
from app.crud.sleeper.trade import get_trade_signals
from app.schemas.trades import (
    BulkTradeAvailabilityResponse,
    BulkTradePlayerSearchResult,
    BulkTradeProposalRequest,
    BulkTradeProposalResponse,
    TradeDirection,
)
from app.services.trades.bulk import (
    get_bulk_trade_availability,
    search_bulk_trade_players,
    submit_bulk_trade_offers,
)

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

@router.get(
    "/bulk/search",
    response_model=list[BulkTradePlayerSearchResult],
)
async def bulk_trade_player_search_endpoint(
    q: str = Query(
        ...,
        min_length=2,
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=25,
    ),
    ctx: Context = Depends(get_context),
) -> list[BulkTradePlayerSearchResult]:
    return await search_bulk_trade_players(
        db=ctx.db,
        query=q,
        limit=limit,
    )


@router.get(
    "/bulk/availability",
    response_model=BulkTradeAvailabilityResponse,
)
async def bulk_trade_availability_endpoint(
    player_id: str = Query(
        ...,
        description=(
            "Sleeper player ID selected from database search."
        ),
    ),
    direction: TradeDirection = Query(
        ...,
    ),
    pick_season: str = Query(
        ...,
        min_length=4,
        max_length=4,
        description=(
            "Draft-pick year, such as 2026."
        ),
    ),
    pick_round: int = Query(
        ...,
        ge=1,
        le=10,
        description=(
            "Draft-pick round, such as 2."
        ),
    ),
    ctx: Context = Depends(get_context),
) -> BulkTradeAvailabilityResponse:
    if ctx.connection is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Connect a Sleeper account before checking "
                "bulk trade availability."
            ),
        )

    return await get_bulk_trade_availability(
        db=ctx.db,
        connection=ctx.connection,
        sleeper=ctx.sleeper,
        player_id=player_id,
        direction=direction,
        pick_season=pick_season,
        pick_round=pick_round,
    )


@router.post(
    "/bulk/propose",
    response_model=BulkTradeProposalResponse,
    status_code=status.HTTP_200_OK,
)
async def submit_bulk_trade_offers_endpoint(
    body: BulkTradeProposalRequest,
    ctx: Context = Depends(get_context),
) -> BulkTradeProposalResponse:
    return await submit_bulk_trade_offers(
        db=ctx.db,
        connection=ctx.connection,
        sleeper=ctx.sleeper,
        request=body,
    )