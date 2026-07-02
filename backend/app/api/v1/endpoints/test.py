from fastapi import APIRouter, Depends

from app.core.context import Context
from app.api.deps import get_context

router = APIRouter()


from app.integrations.sleeper.schemas.api import Projection

@router.get(
    "/projections",
    response_model=Projection,
)
async def test_projections(
    ctx: Context = Depends(get_context),
):

    projections = await ctx.sleeper.read.get_projections(
        2026
    )

    return {
        "projections": projections[:10]
    }


from app.services.sleeper.projection import sync_projections

@router.post("/sync-projections")
async def sync_projection_endpoint(
    ctx: Context = Depends(get_context)
):

    await sync_projections(
        db=ctx.db,
        sleeper=ctx.sleeper,
        season=2026,
        force_update=True,
    )

    return {
        "status": "complete"
    }


from app.analytics.war.redraft.service import WARService

@router.get("/war")
async def test_war(
    ctx: Context = Depends(get_context),
):

    results = await WARService().calculate(
        ctx.db,
        league_id="1312499253972602880",
    )

    # 1312145367281700864 14 team best ball
    # 1312499253972602880 12 team best ball
    
    return [
        {
            "name": r.name,
            "position": r.position,
            "team": r.team,
            "projection": r.projection,
            
            "starter_war": r.starter_war,
            "starter_replacement": r.starter_replacement,
            
            "roster_war": r.roster_war,
            "roster_replacement": r.roster_replacement,
        }
        #for r in (results[:500])
        for r in (results[:50] + results[250:300])
    ]


from app.crud.ktc.sync import sync_ktc_values

@router.get("/ktc_sync")
async def ktc_sync(
    ctx: Context = Depends(get_context),
):

    return await sync_ktc_values(
        db=ctx.db,
        ktc=ctx.ktc
    )


from app.crud.underdog.sync import sync_underdog_adp

@router.get("/underdog_sync")
async def underdog_sync(
    ctx: Context = Depends(get_context),
):

    return await sync_underdog_adp(
        db=ctx.db,
        underdog=ctx.underdog
    )


from app.crud.fc.sync import sync_fantasycalc_values

@router.get("/fc_sync")
async def fc_sync(
    ctx: Context = Depends(get_context),
):

    return await sync_fantasycalc_values(
        db=ctx.db,
        fc=ctx.fc
    )


from app.crud.value import get_player_values

@router.get("/dynasty_phase5")
async def dynasty_phase5(
    ctx: Context = Depends(get_context),
):

    league_id = "1312499253972602880"

    war_players = await WARService().calculate(
        ctx.db,
        league_id=league_id,
    )

    values = await get_player_values(
        ctx.db,
        player_ids=[
            p.player_id 
            for p in war_players
        ],
        war_players=war_players,
    )

    values.sort(
        key=lambda x: x.roster_war or 0,
        reverse=True,
    )

    return values[:50]


from app.services.leagues.overview import LeagueOverview

@router.get("/league_overview/{username}")
async def league_overview(
    username: str,
    ctx: Context = Depends(get_context),
):

    return await LeagueOverview().get_league_overview(
        ctx.db,
        username=username,
    )


from app.services.leagues.details import LeagueDetails

@router.get("/league_details/{league_id}")
async def league_details(
    league_id: str,
    ctx: Context = Depends(get_context),
):

    return await LeagueDetails().get_league_details(
        ctx.db,
        league_id=league_id,
    )


from app.services.dashboard.service import get_user_dashboard

@router.get("/dashboard/{username}")
async def dashboard(
    username: str,
    ctx: Context = Depends(get_context),
):

    return await get_user_dashboard(
        ctx.db,
        username,
    )