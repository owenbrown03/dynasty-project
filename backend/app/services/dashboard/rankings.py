from __future__ import annotations


def get_sortable_value(
    item: dict,
    value_key: str,
) -> float:
    """
    Converts a dashboard metric into a sortable number.

    Missing values rank as zero. This avoids dashboard-wide crashes if a
    future metric is unavailable for a player or league.
    """

    value = item.get(
        value_key,
    )

    if value is None:
        return 0.0

    return float(value)


def add_rank(
    items: list[dict],
    value_key: str,
    rank_key: str,
    *,
    reverse: bool = True,
) -> None:
    """
    Assigns ordinal ranks.

    This keeps your original ranking behavior:
    - larger value is better for KTC, FC, and WAR
    - smaller value is better for average age
    """

    ranked = sorted(
        items,
        key=lambda item: get_sortable_value(
            item,
            value_key,
        ),
        reverse=reverse,
    )

    for index, item in enumerate(
        ranked,
        start=1,
    ):
        item[rank_key] = index


def rank_league_teams(
    teams: list[dict],
) -> list[dict]:
    standings_ranked = sorted(
        teams,
        key=lambda item: (
            int(item.get("wins", 0)),
            -int(item.get("losses", 0)),
            get_sortable_value(
                item,
                "points_for",
            ),
            -int(item.get("roster_id", 0)),
        ),
        reverse=True,
    )

    for index, item in enumerate(
        standings_ranked,
        start=1,
    ):
        item["standings_rank"] = index

    add_rank(
        teams,
        "ktc_value",
        "ktc_rank",
    )

    add_rank(
        teams,
        "fc_value",
        "fc_rank",
    )

    add_rank(
        teams,
        "dynasty_starter_war",
        "dynasty_starter_war_rank",
    )

    add_rank(
        teams,
        "dynasty_roster_war",
        "dynasty_roster_war_rank",
    )

    add_rank(
        teams,
        "redraft_starter_war",
        "redraft_starter_war_rank",
    )

    add_rank(
        teams,
        "redraft_roster_war",
        "redraft_roster_war_rank",
    )

    add_rank(
        teams,
        "average_age",
        "age_rank",
        reverse=False,
    )

    add_rank(
        teams,
        "points_for",
        "points_for_rank",
    )

    return teams
