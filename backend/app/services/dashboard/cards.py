from __future__ import annotations

import logging
from statistics import mean

from .rankings import (
    rank_league_teams,
)


logger = logging.getLogger(__name__)


def sum_player_metric(
    players,
    metric_name: str,
) -> float:
    """
    Adds a player metric while treating missing values as zero.

    Missing dynasty values are expected for non-QB/RB/WR/TE players.
    """

    return sum(
        getattr(
            player,
            metric_name,
            None,
        )
        or 0
        for player in players
    )


def build_team_metrics(
    *,
    roster,
    player_map,
) -> dict:
    """
    Builds one team's cross-metric totals in one specific league.
    """

    players = [
        player_map[player_id]
        for player_id in (roster.players or [])
        if player_id in player_map
    ]

    ages = [
        player.age
        for player in players
        if player.age is not None
    ]

    return {
        "owner_id": roster.owner_id,
        "wins": roster.wins,
        "losses": roster.losses,
        "ties": roster.ties,

        "player_count": len(players),

        "ktc_value": sum_player_metric(
            players,
            "ktc_value",
        ),

        "fc_value": sum_player_metric(
            players,
            "fc_value",
        ),

        "dynasty_starter_war": sum_player_metric(
            players,
            "dynasty_starter_war",
        ),

        "dynasty_roster_war": sum_player_metric(
            players,
            "dynasty_roster_war",
        ),

        "redraft_starter_war": sum_player_metric(
            players,
            "redraft_starter_war",
        ),

        "redraft_roster_war": sum_player_metric(
            players,
            "redraft_roster_war",
        ),

        "average_age": (
            mean(ages)
            if ages
            else None
        ),
    }


def build_league_cards(
    *,
    leagues,
    all_rosters,
    player_maps_by_league_id,
    user_id,
):
    """
    Builds one dashboard card per league.

    Each league receives its own PlayerValue map because WAR is not global.
    """

    output = []

    for league_id, data in leagues.items():
        league = data["league"]

        league_rosters = all_rosters.get(
            league_id,
            [],
        )

        player_map = player_maps_by_league_id.get(
            league_id,
            {},
        )

        teams = [
            build_team_metrics(
                roster=roster,
                player_map=player_map,
            )
            for roster in league_rosters
        ]

        if not teams:
            logger.warning(
                "Skipping dashboard league=%s because no rosters were found",
                league_id,
            )
            continue

        rank_league_teams(
            teams,
        )

        mine = next(
            (
                team
                for team in teams
                if team["owner_id"] == user_id
            ),
            None,
        )

        if mine is None:
            logger.warning(
                (
                    "Skipping dashboard league=%s because user=%s "
                    "does not own a roster in the loaded data"
                ),
                league_id,
                user_id,
            )
            continue

        output.append(
            {
                "league_id": league_id,
                "league_name": league.name,
                "avatar": league.avatar,

                "league_size": len(teams),
                "wins": mine["wins"],
                "losses": mine["losses"],
                "ties": mine["ties"],

                "ktc_value": mine["ktc_value"],
                "ktc_rank": mine["ktc_rank"],

                "fc_value": mine["fc_value"],
                "fc_rank": mine["fc_rank"],

                "dynasty_starter_war": (
                    mine["dynasty_starter_war"]
                ),
                "dynasty_starter_war_rank": (
                    mine["dynasty_starter_war_rank"]
                ),

                "dynasty_roster_war": (
                    mine["dynasty_roster_war"]
                ),
                "dynasty_roster_war_rank": (
                    mine["dynasty_roster_war_rank"]
                ),

                "redraft_starter_war": (
                    mine["redraft_starter_war"]
                ),
                "redraft_starter_war_rank": (
                    mine["redraft_starter_war_rank"]
                ),

                "redraft_roster_war": (
                    mine["redraft_roster_war"]
                ),
                "redraft_roster_war_rank": (
                    mine["redraft_roster_war_rank"]
                ),

                "average_age": mine["average_age"],
                "age_rank": mine["age_rank"],
            }
        )

    return output
