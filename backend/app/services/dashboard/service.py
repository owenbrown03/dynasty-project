import logging

from .crud import (
    get_user_by_name,
    get_user_leagues,
    get_all_league_rosters,
)

from .cards import (
    build_league_cards,
)

from .summary import (
    build_summary,
)

from .top_assets import (
    build_top_assets,
)

from app.crud.value import (
    get_player_values,
)

from app.analytics.war.redraft.service import (
    WARService,
)


logger = logging.getLogger(__name__)



async def get_user_dashboard(
    db,
    username: str,
):


    # -----------------------------
    # User
    # -----------------------------

    user = await get_user_by_name(
        db,
        username,
    )


    if not user:
        raise ValueError(
            f"User {username} not found"
        )



    # -----------------------------
    # Leagues
    # -----------------------------

    leagues = await get_user_leagues(
        db,
        user.user_id,
    )


    if not leagues:
        return {
            "summary": {},
            "leagues": [],
            "top_assets": [],
        }



    league_ids = list(
        leagues.keys()
    )


    all_rosters = await get_all_league_rosters(
        db,
        league_ids,
    )



    # -----------------------------
    # WAR
    # -----------------------------

    war_service = WARService()


    war_players = []


    for league_id in league_ids:

        results = await war_service.calculate(
            db,
            league_id,
        )

        war_players.extend(
            results
        )



    # -----------------------------
    # Players
    # -----------------------------

    player_ids=set()


    for rosters in all_rosters.values():

        for roster in rosters:

            player_ids.update(
                roster.players or []
            )


    player_values = await get_player_values(
        db,
        player_ids,
        war_players,
    )


    player_map = {
        p.player_id:p
        for p in player_values
    }



    # -----------------------------
    # Build output
    # -----------------------------

    league_cards = build_league_cards(
        leagues,
        all_rosters,
        player_map,
        user.user_id,
    )


    summary = build_summary(
        league_cards,
        player_values,
    )


    top_assets = build_top_assets(
        player_values,
    )


    return {

        "summary": summary,

        "leagues": league_cards,

        "top_assets": top_assets,
    }