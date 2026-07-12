from fastapi import (
    APIRouter,
    status,
    Query,
)


from app.api.deps import (
    ContextDep,
    require_sleeper_connection,
)
from app.crud.sleeper.trade import get_trade_signals
from app.schemas.trades import (
    BulkTradeAvailabilityResponse,
    BulkTradePlayerSearchResult,
    BulkTradeProposalRequest,
    BulkTradeProposalResponse,
    TradeCalculatorPickValueResponse,
    TradeDirection,
)
from app.services.trades.bulk import (
    get_bulk_trade_availability,
    search_bulk_trade_players,
    submit_bulk_trade_offers,
)
from app.services.trades.calculator import (
    get_trade_calculator_pick_value,
)
from app.tasks.trade import sync_leaguemates_task

router = APIRouter()

@router.get("/{username}/trade-signals")
async def get_trade_signals_endpoint(
    username: str,
    ctx: ContextDep,
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
    ctx: ContextDep,
    q: str = Query(
        ...,
        min_length=2,
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=25,
    ),
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
    ctx: ContextDep,
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
) -> BulkTradeAvailabilityResponse:
    require_sleeper_connection(
        ctx,
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
    ctx: ContextDep,
) -> BulkTradeProposalResponse:
    require_sleeper_connection(
        ctx,
        detail=(
            "Connect a Sleeper account before proposing "
            "bulk trades."
        ),
    )

    return await submit_bulk_trade_offers(
        db=ctx.db,
        connection=ctx.connection,
        sleeper=ctx.sleeper,
        request=body,
    )


@router.get(
    "/calculator/pick-value",
    response_model=TradeCalculatorPickValueResponse,
)
async def trade_calculator_pick_value_endpoint(
    ctx: ContextDep,
    season: str = Query(
        ...,
        min_length=4,
        max_length=4,
    ),
    round_number: int = Query(
        ...,
        alias="round",
        ge=1,
        le=10,
    ),
    slot: int | None = Query(
        default=None,
        ge=1,
        le=32,
    ),
    total_rosters: int = Query(
        default=12,
        ge=8,
        le=32,
    ),
    num_qbs: int = Query(
        default=2,
        ge=1,
        le=2,
    ),
    ppr: int = Query(
        default=1,
        ge=0,
        le=2,
    ),
) -> TradeCalculatorPickValueResponse:
    return await get_trade_calculator_pick_value(
        ctx.db,
        season=season,
        round_number=round_number,
        slot=slot,
        total_rosters=total_rosters,
        num_qbs=num_qbs,
        ppr=ppr,
    )
