from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable

from app.analytics.war.dynasty.factory import (
    build_dynasty_war_service,
)
from app.analytics.war.redraft.singleton import (
    war_service,
)
from app.crud.value import (
    get_player_values,
)
from app.services.waivers.dynasty import (
    DYNASTY_FANTASY_POSITIONS,
    build_dynasty_projection,
)

from .cards import (
    build_league_cards,
)
from .crud import (
    get_all_league_rosters,
)
from .summary import (
    build_summary,
)
from .top_assets import (
    build_top_assets,
)
from app.services.leagues.selection import (
    get_visible_owned_league_rows_by_sleeper_user_id,
)
from app.crud.sleeper.personal import get_league_sort_orders
from app.crud.sleeper.user import get_userid_by_username


logger = logging.getLogger(__name__)

CURRENT_DASHBOARD_STATUSES = {
    "pre_draft",
    "drafting",
    "in_season",
    "post_season",
}


def get_league_season(
    league,
) -> int:
    """
    Converts the DB league season into the integer used by WAR projections.

    Keeping this isolated makes errors easier to diagnose if old leagues
    or malformed season data ever enter the dashboard query.
    """

    try:
        return int(league.season)
    except (
        TypeError,
        ValueError,
    ) as error:
        raise ValueError(
            f"League {league.league_id} has invalid season "
            f"{league.season!r}"
        ) from error


def build_league_rostered_player_ids(
    rosters,
    league_war_by_player_id,
) -> set[str]:
    """
    Returns all rostered players who exist in the league's WAR universe.

    We intentionally do not restrict this function to QB/RB/WR/TE because
    KTC, FantasyCalc, roster counts, and player counts should still include
    any rostered player that has a value record.

    Dynasty projection filtering happens separately.
    """

    return {
        player_id
        for roster in rosters
        for player_id in (roster.players or [])
        if player_id in league_war_by_player_id
    }


def build_dynasty_war_by_player_id(
    *,
    league_war_by_player_id,
    rostered_player_ids: Iterable[str],
    dynasty_service,
):
    """
    Builds dynasty WAR only for players currently rostered in this league.

    Dynasty WAR is league-context-specific because the input redraft WAR
    already reflects that league's scoring, lineup requirements, and
    replacement levels.
    """

    dynasty_war_by_player_id = {}

    for player_id in rostered_player_ids:
        player_war = league_war_by_player_id.get(
            player_id,
        )

        if player_war is None:
            continue

        if (
            player_war.position
            not in DYNASTY_FANTASY_POSITIONS
        ):
            continue

        projection = build_dynasty_projection(
            player_war=player_war,
            dynasty_service=dynasty_service,
        )

        if projection is not None:
            dynasty_war_by_player_id[
                player_id
            ] = projection

    return dynasty_war_by_player_id


async def load_shared_war_data_by_season(
    *,
    db,
    leagues,
) -> dict[int, object]:
    """
    WAR shared data is season-specific.

    Most dashboard users will only have one season, but grouping by season
    prevents an old league from accidentally using current-season shared
    projections or replacement data.
    """

    seasons = sorted(
        {
            get_league_season(
                league_data["league"],
            )
            for league_data in leagues.values()
        }
    )

    shared_results = await asyncio.gather(
        *[
            war_service.load_shared_data(
                db,
                season,
            )
            for season in seasons
        ]
    )

    return dict(
        zip(
            seasons,
            shared_results,
        )
    )


async def calculate_war_by_league(
    *,
    leagues,
    shared_by_season,
) -> dict[str, list]:
    """
    Calculates redraft WAR independently for every league.

    Do not flatten these results into one global player map afterward.
    The same player can have different WAR values across leagues.
    """

    league_ids = list(
        leagues.keys(),
    )

    tasks = [
        war_service.calculate_with_data(
            league=leagues[league_id]["league"],
            shared=shared_by_season[
                get_league_season(
                    leagues[league_id]["league"],
                )
            ],
        )
        for league_id in league_ids
    ]

    results_per_league = await asyncio.gather(
        *tasks,
        return_exceptions=False,
    )

    return dict(
        zip(
            league_ids,
            results_per_league,
        )
    )


async def build_player_maps_by_league(
    *,
    db,
    leagues,
    all_rosters,
    war_results_by_league_id,
) -> dict[str, dict]:
    """
    Builds:

        {
            league_id: {
                player_id: PlayerValue,
            },
        }

    Every PlayerValue in a league map contains:
    - market values
    - redraft WAR for that exact league
    - dynasty WAR projected from that exact league's redraft WAR
    """

    dynasty_service = build_dynasty_war_service()

    player_maps_by_league_id = {}

    for league_id in leagues:
        league_war_players = war_results_by_league_id[
            league_id
        ]

        league_war_by_player_id = {
            player.player_id: player
            for player in league_war_players
        }

        league_rosters = all_rosters.get(
            league_id,
            [],
        )

        rostered_player_ids = (
            build_league_rostered_player_ids(
                rosters=league_rosters,
                league_war_by_player_id=(
                    league_war_by_player_id
                ),
            )
        )

        dynasty_war_by_player_id = (
            build_dynasty_war_by_player_id(
                league_war_by_player_id=(
                    league_war_by_player_id
                ),
                rostered_player_ids=(
                    rostered_player_ids
                ),
                dynasty_service=dynasty_service,
            )
        )

        league_player_values = await get_player_values(
            db=db,
            player_ids=rostered_player_ids,
            redraft_war_players=league_war_players,
            dynasty_war_by_player_id=(
                dynasty_war_by_player_id
            ),
        )

        player_maps_by_league_id[league_id] = {
            player.player_id: player
            for player in league_player_values
        }

        logger.info(
            (
                "Dashboard values league=%s "
                "rostered=%s dynasty_projected=%s enriched=%s"
            ),
            league_id,
            len(rostered_player_ids),
            len(dynasty_war_by_player_id),
            len(league_player_values),
        )

    return player_maps_by_league_id


def flatten_player_maps(
    player_maps_by_league_id,
) -> list:
    """
    Keeps player values in their original league context.

    A player rostered in multiple leagues intentionally appears multiple
    times here because their WAR can differ per league.
    """

    return [
        player
        for player_map in (
            player_maps_by_league_id.values()
        )
        for player in player_map.values()
    ]


async def get_user_dashboard(
    db,
    redis,
    sleeper,
    username: str,
    *,
    site_user_id=None,
):
    """
    Returns the user's cross-league dashboard.

    Redis stays in the signature because this service is part of the
    dashboard API contract, even though calculate_with_data() uses already
    loaded shared WAR data and does not need Redis directly.
    """

    del redis

    user_id = await get_userid_by_username(
        db,
        sleeper,
        username,
    )

    sort_order = await get_league_sort_orders(
        db=db,
        user_id=user_id,
    )

    visible_rows = await get_visible_owned_league_rows_by_sleeper_user_id(
        db=db,
        sleeper_user_id=user_id,
        site_user_id=site_user_id,
    )
    current_rows = [
        row
        for row in visible_rows
        if row.league.status in CURRENT_DASHBOARD_STATUSES
    ]

    selected_rows = (
        current_rows
        if current_rows
        else visible_rows
    )

    leagues = {
        row.league.league_id: {
            "league": row.league,
            "user_rosters": [row.roster],
        }
        for row in selected_rows
    }

    if not leagues:
        return {
            "summary": {},
            "leagues": [],
            "top_assets": [],
        }

    league_ids = list(
        leagues.keys(),
    )

    all_rosters = await get_all_league_rosters(
        db,
        league_ids,
    )

    shared_by_season = (
        await load_shared_war_data_by_season(
            db=db,
            leagues=leagues,
        )
    )

    war_results_by_league_id = (
        await calculate_war_by_league(
            leagues=leagues,
            shared_by_season=shared_by_season,
        )
    )

    player_maps_by_league_id = (
        await build_player_maps_by_league(
            db=db,
            leagues=leagues,
            all_rosters=all_rosters,
            war_results_by_league_id=(
                war_results_by_league_id
            ),
        )
    )

    all_player_values = flatten_player_maps(
        player_maps_by_league_id,
    )

    league_cards = build_league_cards(
        leagues=leagues,
        all_rosters=all_rosters,
        player_maps_by_league_id=(
            player_maps_by_league_id
        ),
        user_id=user_id,
    )
    league_cards.sort(
        key=lambda league: (
            sort_order.get(league["league_id"], 9999),
            league["league_name"].lower(),
        ),
    )

    summary = build_summary(
        league_cards=league_cards,
        all_players=all_player_values,
    )

    top_assets = build_top_assets(
        players=all_player_values,
    )

    return {
        "summary": summary,
        "leagues": league_cards,
        "top_assets": top_assets,
    }
