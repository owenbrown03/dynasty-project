def add_rank(
    items,
    value_key,
    rank_key,
    reverse=True,
):

    ranked = sorted(
        items,
        key=lambda x: (
            x[value_key]
            if x[value_key] is not None
            else 0
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
):

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
        "starter_war",
        "starter_war_rank",
    )


    add_rank(
        teams,
        "roster_war",
        "roster_war_rank",
    )


    # younger is better
    add_rank(
        teams,
        "average_age",
        "age_rank",
        reverse=False,
    )


    return teams