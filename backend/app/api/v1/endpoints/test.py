from fastapi import APIRouter

from app.analytics.war.redraft.service import WARService
from app.api.deps import ContextDep
from app.crud.fc.sync import sync_fantasycalc_values
from app.crud.ktc.sync import sync_ktc_values
from app.crud.underdog.sync import sync_underdog_adp
from app.crud.value import get_player_values
from app.integrations.sleeper.schemas.api import Projection
from app.services.dashboard.service import get_user_dashboard
from app.services.leagues.details import LeagueDetails
from app.services.leagues.overview import get_league_overview
from app.services.sleeper.projection import sync_projections

router = APIRouter()

@router.get(
    "/projections",
    response_model=Projection,
)
async def test_projections(
    ctx: ContextDep,
):
    projections = await ctx.sleeper.read.get_projections(
        2026
    )

    return {
        "projections": projections[:10]
    }

@router.post("/sync-projections")
async def sync_projection_endpoint(
    ctx: ContextDep,
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

@router.get("/war")
async def test_war(
    ctx: ContextDep,
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

@router.get("/ktc_sync")
async def ktc_sync(
    ctx: ContextDep,
):
    return await sync_ktc_values(
        db=ctx.db,
        ktc=ctx.ktc
    )

@router.get("/underdog_sync")
async def underdog_sync(
    ctx: ContextDep,
):
    return await sync_underdog_adp(
        db=ctx.db,
        underdog=ctx.underdog
    )

@router.get("/fc_sync")
async def fc_sync(
    ctx: ContextDep,
):
    return await sync_fantasycalc_values(
        db=ctx.db,
        fc=ctx.fc
    )

@router.get("/dynasty_phase5")
async def dynasty_phase5(
    ctx: ContextDep,
):
    league_id = "1312499253972602880"

    war_players = await WARService().calculate(
        ctx.db,
        ctx.redis,
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

@router.get("/league_overview/{username}")
async def league_overview(
    username: str,
    ctx: ContextDep,
):
    return await get_league_overview(
        ctx.db,
        username=username,
    )

@router.get("/league_details/{league_id}")
async def league_details(
    league_id: str,
    ctx: ContextDep,
):
    return await LeagueDetails().get_league_details(
        ctx.db,
        ctx.redis,
        league_id=league_id,
    )

@router.get("/dashboard/{username}")
async def dashboard(
    username: str,
    ctx: ContextDep,
):
    return await get_user_dashboard(
        ctx.db,
        ctx.redis,
        username,
    )
