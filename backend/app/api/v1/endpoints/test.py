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


from app.analytics.player_value.service import WARService

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
            "replacement": r.replacement,
            "war": r.war,
        }
        for r in results[:50]
    ]


from app.analytics.player_value.dynasty.discount import DiscountCurve
from app.analytics.player_value.dynasty.expected_games import (
    ExpectedGamesRemainingService,
)

@router.get("/dynasty_phase1")
async def dynasty_phase1():

    expected = ExpectedGamesRemainingService().calculate(
        age=24.7,
        position="RB",
    )

    discount = DiscountCurve()

    return {
        "expected_games": expected.model_dump(),

        "discount_curve": {
            "today": discount.weight(0),
            "1_game": discount.weight(1),
            "8_games": discount.weight(8),
            "17_games": discount.weight(17),
            "34_games": discount.weight(34),
            "68_games": discount.weight(68),
            "136_games": discount.weight(136),
        },
    }


from app.analytics.player_value.dynasty.projector import WARProjector
from app.analytics.player_value.dynasty.expected_games import ExpectedGamesRemainingService
from app.analytics.player_value.dynasty.aging import AgingCurve
from app.analytics.player_value.dynasty.discount import DiscountCurve

@router.get("/dynasty_phase2")
async def dynasty_phase2():

    projector = WARProjector(
        expected_games_service=ExpectedGamesRemainingService(),
        aging_curve=AgingCurve(),
        discount_curve=DiscountCurve(),
    )

    result = projector.project(
        war=5.0,
        age=24.7,
        position="RB",
    )

    return {
        "input": {
            "war": 5.0,
            "age": 24.7,
            "position": "RB",
        },
        "result": {
            "future_war": result.future_war,
            "expected_games": result.expected_games,
            "seasons_remaining": result.seasons_remaining,
        },
    }


from app.analytics.player_value.dynasty.service import DynastyWARService

@router.get("/dynasty_phase3")
async def dynasty_phase3():

    service = DynastyWARService(
        projector=WARProjector(
            expected_games_service=ExpectedGamesRemainingService(),
            aging_curve=AgingCurve(),
            discount_curve=DiscountCurve(),
        )
    )

    result = service.project_player(
        player_id="123",
        name="Test RB",
        age=24.7,
        position="RB",
        war=5.0,
    )

    return {
        "result": {
            "player_id": result.player_id,
            "name": result.name,
            "position": result.position,
            "age": result.age,
            "future_war": result.future_war,
            "total_war": result.total_war,
            "expected_games": result.expected_games,
            "seasons_remaining": result.seasons_remaining,
        }
    }


@router.get("/dynasty_phase3_batch")
async def dynasty_phase3_batch():

    service = DynastyWARService(
        projector=WARProjector(
            expected_games_service=ExpectedGamesRemainingService(),
            aging_curve=AgingCurve(),
            discount_curve=DiscountCurve(),
        )
    )

    players = [
        {
            "player_id": "1",
            "name": "Young RB",
            "age": 23,
            "position": "RB",
            "war": 4.0,
        },
        {
            "player_id": "2",
            "name": "Prime RB",
            "age": 25,
            "position": "RB",
            "war": 5.0,
        },
        {
            "player_id": "3",
            "name": "Aging RB",
            "age": 29,
            "position": "RB",
            "war": 5.0,
        },
        {
            "player_id": "4",
            "name": "Young WR",
            "age": 23,
            "position": "WR",
            "war": 4.0,
        },
    ]

    results = service.project_players(players)

    results.sort(
        key=lambda x: x.future_war,
        reverse=True,
    )

    return {
        "results": [
            {
                "name": player.name,
                "position": player.position,
                "age": player.age,
                "future_war": player.future_war,
                "total_war": player.total_war,
                "expected_games": player.expected_games,
            }
            for player in results
        ]
    }


from app.analytics.player_value.dynasty.models import DynastyPlayerInput
from app.analytics.player_value.dynasty.service import DynastyWARService

@router.get("/dynasty_phase4")
async def dynasty_phase4(
    ctx: Context = Depends(get_context),
):

    war_players = await WARService().calculate(
        ctx.db,
        league_id="1312499253972602880",
    )

    dynasty_service = DynastyWARService(
        projector=WARProjector(
            expected_games_service=ExpectedGamesRemainingService(),
            aging_curve=AgingCurve(),
            discount_curve=DiscountCurve(),
        )
    )

    dynasty_results = []

    for player in war_players:

        dynasty_player = DynastyPlayerInput(
            player_id=player.player_id,
            name=player.name,
            position=player.position,
            team=player.team,
            age=player.age,
            war=player.war,
        )

        dynasty_results.append(
            dynasty_service.project_player(
                dynasty_player
            )
        )

    dynasty_results.sort(
        key=lambda x: x.total_war,
        reverse=True,
    )

    return dynasty_results[:50]