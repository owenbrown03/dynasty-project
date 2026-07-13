from fastapi import APIRouter, Query

from app.api.deps import ContextDep
from app.schemas.personal_values import (
    PersonalValueDetailResponse,
    PersonalValuePoolResponse,
    PersonalValueSearchResult,
    PersonalValueUpdateRequest,
)
from app.services.personal_values import (
    get_personal_value_detail,
    get_personal_value_pool,
    save_personal_value_detail,
    search_personal_value_players,
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
