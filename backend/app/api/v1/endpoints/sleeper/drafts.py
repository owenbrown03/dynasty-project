from fastapi import APIRouter, Query

from app.api.deps import (
    ContextDep,
    require_sleeper_connection,
)
from app.schemas.auction import AuctionDraftResponse
from app.schemas.draft import (
    RookieWarHistoryResponse,
    RookieWarHistoryRow,
)
from app.services.auction.draft_center import (
    get_auction_draft_center,
)
from app.services.draft.rookie_war import (
    get_rookie_war_history,
)
from app.services.values.basis import (
    DEFAULT_VALUE_BASIS,
    ValueBasis,
)
from app.services.values.tiers import (
    resolve_league_war_context,
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


@router.get(
    "/rookie-war/history",
    response_model=RookieWarHistoryResponse,
)
async def rookie_war_history_endpoint(
    ctx: ContextDep,
    league_id: str | None = Query(
        default=None,
        description=(
            "Optional league id to compute career WAR under "
            "that league's scoring context. Requires a linked "
            "Sleeper account that owns the league."
        ),
    ),
    rounds: str | None = Query(
        default=None,
        description=(
            "Optional comma-separated list of rookie draft "
            "rounds to include. Defaults to all rounds."
        ),
    ),
):
    league = None
    league_name = None
    war_context = "adp"
    has_war = False

    if league_id:
        league = await resolve_league_war_context(
            ctx=ctx,
            league_id=league_id,
        )
        league_name = league.name
        war_context = "league"
        has_war = True

    parsed_rounds = None
    if rounds:
        parsed_rounds = sorted(
            {
                int(part)
                for part in rounds.split(",")
                if part.strip()
            }
        )

    rows = await get_rookie_war_history(
        db=ctx.db,
        redis=ctx.redis,
        league=league,
        rounds=parsed_rounds,
    )

    return RookieWarHistoryResponse(
        league_id=league_id,
        league_name=league_name,
        war_context=war_context,
        has_war=has_war,
        rounds=parsed_rounds or [],
        rows=[
            RookieWarHistoryRow(**row)
            for row in rows
        ],
    )
