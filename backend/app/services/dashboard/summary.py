from __future__ import annotations

from statistics import mean


def build_summary(
    *,
    league_cards,
    all_players,
):
    """
    Builds totals from the user's league cards.

    WAR totals intentionally sum per-league values. A player rostered in
    multiple leagues should contribute once in each league because each
    roster represents a separate dynasty team.
    """

    ages = [
        player.age
        for player in all_players
        if player.age is not None
    ]

    return {
        "league_count": len(
            league_cards,
        ),

        "player_count": len(
            all_players,
        ),

        "total_ktc_value": sum(
            card["ktc_value"]
            for card in league_cards
        ),

        "total_fc_value": sum(
            card["fc_value"]
            for card in league_cards
        ),

        "total_dynasty_starter_war": round(
            sum(
                card["dynasty_starter_war"]
                for card in league_cards
            ),
            2,
        ),

        "total_dynasty_roster_war": round(
            sum(
                card["dynasty_roster_war"]
                for card in league_cards
            ),
            2,
        ),

        "total_redraft_starter_war": round(
            sum(
                card["redraft_starter_war"]
                for card in league_cards
            ),
            2,
        ),

        "total_redraft_roster_war": round(
            sum(
                card["redraft_roster_war"]
                for card in league_cards
            ),
            2,
        ),

        "average_age": (
            round(
                mean(ages),
                2,
            )
            if ages
            else None
        ),
    }