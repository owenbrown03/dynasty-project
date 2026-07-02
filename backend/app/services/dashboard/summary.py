from statistics import mean


def build_summary(
    league_cards,
    all_players,
):

    ages = [
        p.age
        for p in all_players
        if p.age is not None
    ]


    return {
        "league_count": len(
            league_cards
        ),

        "player_count": len(
            all_players
        ),

        "total_ktc_value": sum(
            x["ktc_value"]
            for x in league_cards
        ),

        "total_fc_value": sum(
            x["fc_value"]
            for x in league_cards
        ),

        "total_starter_war": round(
            sum(
                x["starter_war"]
                for x in league_cards
            ),
            2,
        ),

        "total_roster_war": round(
            sum(
                x["roster_war"]
                for x in league_cards
            ),
            2,
        ),

        "average_age": round(
            mean(ages),
            2,
        )
        if ages
        else None,
    }