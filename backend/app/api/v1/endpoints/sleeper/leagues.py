from fastapi import APIRouter, Depends

from app.core.context import Context
from app.api.deps import get_context

router = APIRouter()


from app.services.leagues.overview import LeagueOverview

@router.get("/overview/{username}")
async def overview_endpoint(
    username: str,
    ctx: Context = Depends(get_context),
):

    return await LeagueOverview().get_league_overview(
        ctx.db,
        username=username,
    )


from app.services.leagues.details import LeagueDetails

@router.get("/details/{league_id}")
async def details_endpoint(
    league_id: str,
    ctx: Context = Depends(get_context),
):

    return await LeagueDetails().get_league_details(
        ctx.db,
        league_id=league_id,
    )


from app.services.dashboard.service import get_user_dashboard

@router.get("/dashboard/{username}")
async def dashboard_endpoint(
    username: str,
    ctx: Context = Depends(get_context),
):

    return await get_user_dashboard(
        ctx.db,
        username,
    )