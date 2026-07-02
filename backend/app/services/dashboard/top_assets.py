def build_top_assets(
    players,
):

    unique = {}

    for player in players:
        unique[
            player.player_id
        ] = player


    top = sorted(
        unique.values(),
        key=lambda x: x.ktc_value or 0,
        reverse=True,
    )[:10]


    return [
        {
            "player_id": p.player_id,
            "name": p.name,
            "position": p.position,
            "team": p.team,

            "ktc_value": p.ktc_value,
            "fc_value": p.fc_value,
            "starter_war": p.starter_war,
            "roster_war": p.roster_war,
        }
        for p in top
    ]