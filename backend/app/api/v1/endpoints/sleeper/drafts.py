from fastapi import APIRouter, Query

from app.api.deps import (
    ContextDep,
    require_sleeper_connection,
)
from app.schemas.auction import AuctionDraftResponse
from app.services.auction.draft_center import (
    get_auction_draft_center,
)
from app.services.values.basis import (
    DEFAULT_VALUE_BASIS,
    ValueBasis,
)

router = APIRouter()


@router.get(
    "/auction-center",
    response_model=AuctionDraftResponse,
)
async def auction_draft_center(
    ctx: ContextDep,
    draft_id: str = Query(
        ...,
        description="Sleeper draft id.",
    ),
    value_basis: ValueBasis = Query(
        default=DEFAULT_VALUE_BASIS,
    ),
    search: str | None = Query(
        default=None,
        description="Optional player-name search.",
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=75,
        ge=1,
        le=200,
    ),
) -> AuctionDraftResponse:
    require_sleeper_connection(
        ctx,
        detail=(
            "Connect a Sleeper account before using "
            "the auction draft center."
        ),
    )

    return await get_auction_draft_center(
        db=ctx.db,
        redis=ctx.redis,
        sleeper=ctx.sleeper,
        connection=ctx.connection,
        draft_id=draft_id,
        value_basis=value_basis,
        search=search,
        page=page,
        page_size=page_size,
    )
