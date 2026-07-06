from __future__ import annotations


def choose_better_asset(
    *,
    current,
    candidate,
):
    """
    KTC is global, so duplicate player rows across leagues normally have
    the same KTC value.

    We retain the row with the stronger KTC value if sources differ, then
    use dynasty roster WAR as a deterministic tie-breaker.
    """

    current_ktc = current.ktc_value or 0
    candidate_ktc = candidate.ktc_value or 0

    if candidate_ktc > current_ktc:
        return candidate

    if candidate_ktc < current_ktc:
        return current

    current_dynasty_war = (
        current.dynasty_roster_war
        or 0
    )

    candidate_dynasty_war = (
        candidate.dynasty_roster_war
        or 0
    )

    if candidate_dynasty_war > current_dynasty_war:
        return candidate

    return current


def build_top_assets(
    *,
    players,
):
    """
    Returns unique players sorted by KTC value.

    Note: Top assets remain a market-value view. The WAR values shown beside
    each player come from one representative league context, so they should
    not be treated as a cross-league universal WAR number.
    """

    unique_by_player_id = {}

    for player in players:
        current = unique_by_player_id.get(
            player.player_id,
        )

        if current is None:
            unique_by_player_id[
                player.player_id
            ] = player
            continue

        unique_by_player_id[
            player.player_id
        ] = choose_better_asset(
            current=current,
            candidate=player,
        )

    top_players = sorted(
        unique_by_player_id.values(),
        key=lambda player: (
            player.ktc_value or 0,
            player.fc_value or 0,
            player.name.lower(),
        ),
        reverse=True,
    )[:10]

    return [
        {
            "player_id": player.player_id,
            "name": player.name,
            "position": player.position,
            "team": player.team,

            "ktc_value": player.ktc_value,
            "fc_value": player.fc_value,

            "dynasty_starter_war": (
                player.dynasty_starter_war
            ),
            "dynasty_roster_war": (
                player.dynasty_roster_war
            ),

            "redraft_starter_war": (
                player.redraft_starter_war
            ),
            "redraft_roster_war": (
                player.redraft_roster_war
            ),
        }
        for player in top_players
    ]