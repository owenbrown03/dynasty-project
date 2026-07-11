from fastapi import APIRouter

from app.api.deps import ContextDep
from app.services.dashboard.service import get_user_dashboard
from app.schemas.league import LeagueOverviewItem
from app.services.leagues.details import LeagueDetails
from app.services.leagues.overview import get_league_overview

router = APIRouter()

@router.get(
    "/overview/{username}",
    response_model=list[LeagueOverviewItem],
)
async def overview_endpoint(
    username: str,
    ctx: ContextDep,
):
    return await get_league_overview(
        ctx.db,
        username=username,
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
