from fastapi import (
    APIRouter,
    Query,
    status,
)

from app.analytics.war.redraft.service import WARService
from app.api.deps import (
    ContextDep,
    require_sleeper_connection,
)
from app.schemas.waivers import (
    BulkWaiverAvailabilityResponse,
    BulkWaiverClaimRequest,
    BulkWaiverClaimResponse,
    BulkWaiverPlayerSearchResult,
    WaiverClaimRequest,
    WaiverClaimResponse,
    WaiverOverviewResponse,
    WaiverRecentlyDroppedResponse,
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
from app.services.waivers.recent_drops import (
    get_recent_drops_sync_required,
    get_recently_dropped_players,
    sync_recent_drop_activity,
)

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
    league_id: str | None = Query(
        default=None,
        description=(
            "Owned Sleeper league whose available players should be shown. "
            "Omit this to aggregate available players across all visible leagues."
        ),
    ),
    value_basis: ValueBasis = Query(
        default=DEFAULT_VALUE_BASIS,
        description=(
            "The player value system used to sort the returned players."
        ),
    ),
) -> WaiverAvailablePlayersResponse:
    require_sleeper_connection(
        ctx,
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
    require_sleeper_connection(
        ctx,
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
    "/recent-drops",
    response_model=WaiverRecentlyDroppedResponse,
)
async def recent_waiver_drops(
    ctx: ContextDep,
    value_basis: ValueBasis = Query(
        default=DEFAULT_VALUE_BASIS,
    ),
) -> WaiverRecentlyDroppedResponse:
    require_sleeper_connection(
        ctx,
        detail=(
            "Connect a Sleeper account before viewing recently dropped players."
        ),
    )

    sync_requested = await get_recent_drops_sync_required(
        db=ctx.db,
        connection=ctx.connection,
    )

    if (
        sync_requested
        and ctx.connection
        and ctx.sleeper
    ):
        await sync_recent_drop_activity(
            db=ctx.db,
            sleeper=ctx.sleeper,
            connection=ctx.connection,
        )

    war_service = WARService()

    return await get_recently_dropped_players(
        db=ctx.db,
        redis=ctx.redis,
        connection=ctx.connection,
        value_basis=value_basis,
        war_service=war_service,
        sync_requested=sync_requested,
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
    require_sleeper_connection(
        ctx,
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
    require_sleeper_connection(
        ctx,
        detail=(
            "Connect a Sleeper account before submitting "
            "bulk waiver claims."
        ),
    )

    return await submit_bulk_claims(
        db=ctx.db,
        connection=ctx.connection,
        sleeper=ctx.sleeper,
        request=body,
    )
