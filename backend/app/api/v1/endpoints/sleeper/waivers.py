from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    status,
)

from app.analytics.war.redraft.service import WARService
from app.api.deps import ContextDep
from app.schemas.waivers import (
    BulkWaiverAvailabilityResponse,
    BulkWaiverClaimRequest,
    BulkWaiverClaimResponse,
    BulkWaiverPlayerSearchResult,
    WaiverClaimRequest,
    WaiverClaimResponse,
    WaiverOverviewResponse,
)
from app.schemas.waivers import (
    WaiverAvailablePlayersResponse,
    WaiverLeagueOption,
    WaiverRosterPlayersResponse,
)
from app.services.waivers.available import (
    get_available_waiver_players,
    get_waiver_league_options,
    get_roster_waiver_players,
)
from app.services.waivers.bulk import (
    get_bulk_waiver_availability,
    search_bulk_waiver_players,
    submit_bulk_claims,
)
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
    ctx: ContextDep,
    value_basis: ValueBasis = Query(
        default=DEFAULT_VALUE_BASIS,
        description=(
            "The player value system used to rank waiver adds "
            "and suggested drops."
        ),
    ),
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
    ctx: ContextDep,
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
    ctx: ContextDep,
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
    ctx: ContextDep,
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
    ctx: ContextDep,
    league_id: str = Query(
        ...,
        description=(
            "Owned Sleeper league whose roster players should be shown."
        ),
    ),
    value_basis: ValueBasis = Query(
        default=DEFAULT_VALUE_BASIS,
    ),
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
    ctx: ContextDep,
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
    ctx: ContextDep,
    player_id: str = Query(
        ...,
        description=(
            "Sleeper player ID to check across every owned league."
        ),
    ),
    value_basis: ValueBasis = Query(
        default=DEFAULT_VALUE_BASIS,
    ),
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
    ctx: ContextDep,
    body: BulkWaiverClaimRequest,
) -> BulkWaiverClaimResponse:
    return await submit_bulk_claims(
        db=ctx.db,
        connection=ctx.connection,
        sleeper=ctx.sleeper,
        request=body,
    )
