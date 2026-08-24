from fastapi import APIRouter, Query

from app.api.deps import ContextDep
from app.schemas.personal_values import (
    PersonalValueDetailResponse,
    PersonalValuePoolResponse,
    PersonalValueRankingsResponse,
    PersonalValueRankingsUpdateRequest,
    PersonalValueRankingsUpdateResponse,
    PersonalValueRankingsResetRequest,
    PersonalValueRankingsResetResponse,
    PersonalValueSearchResult,
    PersonalValueUnderdogSyncRequest,
    PersonalValueUpdateRequest,
)
from app.services.personal_values import (
    get_personal_value_detail,
    get_personal_value_pool,
    get_personal_value_rankings,
    save_personal_value_detail,
    reset_personal_value_rankings,
    search_personal_value_players,
    set_personal_value_rankings,
    sync_underdog_defaults,
)

router = APIRouter()


@router.get(
    "/search",
    response_model=list[PersonalValueSearchResult],
)
async def search_personal_values_players_endpoint(
    ctx: ContextDep,
    query: str = Query(
        min_length=2,
    ),
    league_id: str | None = None,
):
    return await search_personal_value_players(
        ctx=ctx,
        query=query,
        league_id=league_id,
    )


@router.get(
    "/pool",
    response_model=PersonalValuePoolResponse,
)
async def get_personal_value_pool_endpoint(
    league_id: str,
    ctx: ContextDep,
):
    return await get_personal_value_pool(
        ctx=ctx,
        league_id=league_id,
    )


@router.get(
    "/player/{player_id}",
    response_model=PersonalValueDetailResponse,
)
async def get_personal_value_detail_endpoint(
    player_id: str,
    league_id: str,
    ctx: ContextDep,
):
    return await get_personal_value_detail(
        ctx=ctx,
        league_id=league_id,
        player_id=player_id,
    )


@router.post(
    "/player/{player_id}",
    response_model=PersonalValueDetailResponse,
)
async def save_personal_value_detail_endpoint(
    player_id: str,
    league_id: str,
    body: PersonalValueUpdateRequest,
    ctx: ContextDep,
):
    return await save_personal_value_detail(
        ctx=ctx,
        league_id=league_id,
        player_id=player_id,
        payload=body,
    )


@router.get(
    "/rankings",
    response_model=PersonalValueRankingsResponse,
)
async def get_personal_value_rankings_endpoint(
    league_id: str,
    ctx: ContextDep,
    position: str = Query(...),
    scope: str = Query(default="current"),
):
    return await get_personal_value_rankings(
        ctx=ctx,
        league_id=league_id,
        position=position,
        scope=scope,
    )


@router.post(
    "/rankings",
    response_model=PersonalValueRankingsUpdateResponse,
)
async def set_personal_value_rankings_endpoint(
    body: PersonalValueRankingsUpdateRequest,
    ctx: ContextDep,
):
    return await set_personal_value_rankings(
        ctx=ctx,
        request=body,
    )


@router.post(
    "/rankings/reset",
    response_model=PersonalValueRankingsResetResponse,
)
async def reset_personal_value_rankings_endpoint(
    body: PersonalValueRankingsResetRequest,
    ctx: ContextDep,
):
    return await reset_personal_value_rankings(
        ctx=ctx,
        request=body,
    )


@router.post(
    "/rankings/sync-underdog",
    response_model=PersonalValueRankingsResetResponse,
)
async def sync_underdog_defaults_endpoint(
    body: PersonalValueUnderdogSyncRequest,
    ctx: ContextDep,
):
    return await sync_underdog_defaults(
        ctx=ctx,
        league_id=body.league_id,
        position=body.position,
    )

