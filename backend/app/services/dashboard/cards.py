from __future__ import annotations

import logging
from statistics import mean

from app.services.leagues.details import (
    ROSTER_CONSTRUCTION_POSITIONS,
)
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
        "roster_id": roster.roster_id,
        "wins": roster.wins,
        "losses": roster.losses,
        "ties": roster.ties,
        "points_for": roster.fpts,

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


def build_roster_construction_summary(
    *,
    roster,
    player_map,
    roster_construction_targets,
) -> dict[str, float | int] | None:
    if not roster_construction_targets:
        return None

    current_counts = {
        position: 0
        for position in ROSTER_CONSTRUCTION_POSITIONS
    }

    for player_id in roster.players or []:
        player = player_map.get(
            player_id,
        )
        position = getattr(
            player,
            "position",
            None,
        )

        if position in current_counts:
            current_counts[position] += 1

    targets_by_position = {
        target.position: target.target_count
        for target in roster_construction_targets
    }
    total_target_slots = sum(
        targets_by_position.values()
    )

    if total_target_slots <= 0:
        return None

    moves_needed = sum(
        max(
            (targets_by_position.get(position, 0) - current_counts[position]),
            0,
        )
        for position in ROSTER_CONSTRUCTION_POSITIONS
    )
    alignment_pct = max(
        0.0,
        round(
            (1 - (moves_needed / total_target_slots)) * 100,
            1,
        ),
    )

    return {
        "alignment_pct": alignment_pct,
        "moves_needed": moves_needed,
    }


def build_league_cards(
    *,
    leagues,
    all_rosters,
    player_maps_by_league_id,
    roster_construction_targets_by_league_id,
    finance_metrics_by_league_id,
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

        roster_construction_summary = (
            build_roster_construction_summary(
                roster=next(
                    roster
                    for roster in league_rosters
                    if roster.owner_id == user_id
                ),
                player_map=player_map,
                roster_construction_targets=(
                    roster_construction_targets_by_league_id.get(
                        league_id,
                        [],
                    )
                ),
            )
        )
        finance_metrics = finance_metrics_by_league_id.get(
            league_id,
            {},
        )

        output.append(
            {
                "league_id": league_id,
                "league_name": league.name,
                "avatar": league.avatar,

                "league_size": len(teams),
                "wins": mine["wins"],
                "losses": mine["losses"],
                "ties": mine["ties"],
                "standings_rank": mine["standings_rank"],
                "points_for": mine["points_for"],
                "points_for_rank": mine["points_for_rank"],

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
                "projected_payout": finance_metrics.get(
                    "projected_payout",
                ),
                "projected_seed": finance_metrics.get(
                    "projected_seed",
                ),
                "buy_in_amount": finance_metrics.get(
                    "buy_in_amount",
                ),
                "roster_construction_alignment_pct": (
                    roster_construction_summary["alignment_pct"]
                    if roster_construction_summary is not None
                    else None
                ),
                "roster_construction_moves_needed": (
                    roster_construction_summary["moves_needed"]
                    if roster_construction_summary is not None
                    else None
                ),
            }
        )

    return output
