from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from app.analytics.war.redraft.service import WARService
from app.core.context import Context
from app.schemas.waivers import (
    WaiverOverviewResponse,
    WaiverClaimRequest,
    WaiverClaimResponse,
    BulkWaiverAvailabilityResponse,
    BulkWaiverClaimRequest,
    BulkWaiverClaimResponse,
    BulkWaiverPlayerSearchResult,
)
from app.schemas.waivers import (
    WaiverAvailablePlayersResponse,
    WaiverLeagueOption,
    WaiverRosterPlayersResponse,
)
from app.services.waivers.available import (
    get_available_waiver_players,
    get_waiver_league_options,
    get_roster_waiver_players
)
from app.services.waivers.bulk import (
    get_bulk_waiver_availability,
    search_bulk_waiver_players,
    submit_bulk_claims,
)
from app.api.deps import get_context
from app.services.values.basis import (
    DEFAULT_VALUE_BASIS,
    ValueBasis,
)
from app.services.waivers.overview import get_waiver_overview
from app.services.waivers.claims import submit_claim

router = APIRouter()


@router.get(
    "/overview",
    response_model=WaiverOverviewResponse,
)
async def waiver_overview(
    value_basis: ValueBasis = Query(
        default=DEFAULT_VALUE_BASIS,
        description=(
            "The player value system used to rank waiver adds "
            "and suggested drops."
        ),
    ),
    ctx: Context = Depends(get_context),
) -> WaiverOverviewResponse:
    if ctx.connection is None:
        return WaiverOverviewResponse()

    war_service = WARService()

    return await get_waiver_overview(
        db=ctx.db,
        redis=ctx.redis,
        connection=ctx.connection,
        war_service=war_service,
        value_basis=value_basis,
    )


@router.post(
    "/claim",
    response_model=WaiverClaimResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_waiver_claim(
    body: WaiverClaimRequest,
    ctx: Context = Depends(get_context),
) -> WaiverClaimResponse:
    return await submit_claim(
        db=ctx.db,
        connection=ctx.connection,
        sleeper=ctx.sleeper,
        claim=body,
    )

@router.get(
    "/leagues",
    response_model=list[WaiverLeagueOption],
)
async def waiver_leagues(
    ctx: Context = Depends(get_context),
) -> list[WaiverLeagueOption]:
    """
    Supplies the Available Players league dropdown.
    """

    if ctx.connection is None:
        return []

    return await get_waiver_league_options(
        db=ctx.db,
        connection=ctx.connection,
    )


@router.get(
    "/available",
    response_model=WaiverAvailablePlayersResponse,
)
async def available_waiver_players(
    league_id: str = Query(
        ...,
        description=(
            "Owned Sleeper league whose available players should be shown."
        ),
    ),
    value_basis: ValueBasis = Query(
        default=DEFAULT_VALUE_BASIS,
        description=(
            "The player value system used to sort the returned players."
        ),
    ),
    ctx: Context = Depends(get_context),
) -> WaiverAvailablePlayersResponse:
    if ctx.connection is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Connect a Sleeper account before viewing "
                "available players."
            ),
        )

    war_service = WARService()

    return await get_available_waiver_players(
        db=ctx.db,
        redis=ctx.redis,
        connection=ctx.connection,
        league_id=league_id,
        value_basis=value_basis,
        war_service=war_service,
    )


@router.get(
    "/roster-players",
    response_model=WaiverRosterPlayersResponse,
)
async def roster_waiver_players(
    league_id: str = Query(
        ...,
        description=(
            "Owned Sleeper league whose roster players should be shown."
        ),
    ),
    value_basis: ValueBasis = Query(
        default=DEFAULT_VALUE_BASIS,
    ),
    ctx: Context = Depends(get_context),
) -> WaiverRosterPlayersResponse:
    if ctx.connection is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Connect a Sleeper account before viewing roster players."
            ),
        )

    war_service = WARService()

    return await get_roster_waiver_players(
        db=ctx.db,
        redis=ctx.redis,
        connection=ctx.connection,
        league_id=league_id,
        value_basis=value_basis,
        war_service=war_service,
    )


@router.get(
    "/bulk/search",
    response_model=list[BulkWaiverPlayerSearchResult],
)
async def bulk_waiver_player_search(
    q: str = Query(
        ...,
        min_length=2,
        description=(
            "Player name to search before checking bulk "
            "waiver availability."
        ),
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=25,
    ),
    ctx: Context = Depends(get_context),
) -> list[BulkWaiverPlayerSearchResult]:
    return await search_bulk_waiver_players(
        db=ctx.db,
        query=q,
        limit=limit,
    )


@router.get(
    "/bulk/availability",
    response_model=BulkWaiverAvailabilityResponse,
)
async def bulk_waiver_availability(
    player_id: str = Query(
        ...,
        description=(
            "Sleeper player ID to check across every owned league."
        ),
    ),
    value_basis: ValueBasis = Query(
        default=DEFAULT_VALUE_BASIS,
    ),
    ctx: Context = Depends(get_context),
) -> BulkWaiverAvailabilityResponse:
    if ctx.connection is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Connect a Sleeper account before checking "
                "bulk waiver availability."
            ),
        )

    war_service = WARService()

    return await get_bulk_waiver_availability(
        db=ctx.db,
        redis=ctx.redis,
        connection=ctx.connection,
        player_id=player_id,
        value_basis=value_basis,
        war_service=war_service,
    )


@router.post(
    "/bulk/claim",
    response_model=BulkWaiverClaimResponse,
    status_code=status.HTTP_200_OK,
)
async def submit_bulk_waiver_claims(
    body: BulkWaiverClaimRequest,
    ctx: Context = Depends(get_context),
) -> BulkWaiverClaimResponse:
    return await submit_bulk_claims(
        db=ctx.db,
        connection=ctx.connection,
        sleeper=ctx.sleeper,
        request=body,
    )