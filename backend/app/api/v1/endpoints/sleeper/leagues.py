from fastapi import APIRouter, Query

from app.api.deps import ContextDep
from app.services.dashboard.service import get_user_dashboard
from app.schemas.league import (
    LeagueOverviewItem,
    LeagueVisibilityItem,
    LeagueVisibilityUpdate,
)
from app.services.leagues.details import LeagueDetails
from app.services.leagues.overview import get_league_overview
from app.services.leagues.visibility import (
    set_league_visibility,
)

router = APIRouter()

@router.get(
    "/overview/{username}",
    response_model=list[LeagueOverviewItem],
)
async def overview_endpoint(
    username: str,
    ctx: ContextDep,
    include_hidden: bool = Query(default=False),
):
    return await get_league_overview(
        ctx.db,
        username=username,
        site_user_id=(
            ctx.site_user.id
            if ctx.site_user is not None
            else None
        ),
        include_hidden=include_hidden,
    )

@router.get("/details/{league_id}")
async def details_endpoint(
    league_id: str,
    ctx: ContextDep,
):
    return await LeagueDetails().get_league_details(
        ctx.db,
        ctx.redis,
        league_id=league_id,
        site_user_id=(
            ctx.site_user.id
            if ctx.site_user is not None
            else None
        ),
    )

@router.get("/dashboard/{username}")
async def dashboard_endpoint(
    username: str,
    ctx: ContextDep,
):
    return await get_user_dashboard(
        ctx.db,
        ctx.redis,
        username,
    )


@router.put(
    "/visibility/{league_id}",
    response_model=LeagueVisibilityItem,
)
async def visibility_endpoint(
    league_id: str,
    body: LeagueVisibilityUpdate,
    ctx: ContextDep,
):
    return await set_league_visibility(
        ctx=ctx,
        league_id=league_id,
        hidden=body.hidden,
    )
