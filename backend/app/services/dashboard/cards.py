from statistics import mean

from .rankings import rank_league_teams



def build_league_cards(
    leagues,
    all_rosters,
    player_map,
    user_id,
):

    output=[]


    for league_id,data in leagues.items():

        teams=[]


        for roster in all_rosters[league_id]:

            players=[]


            for player_id in roster.players or []:

                player = player_map.get(
                    player_id
                )

                if player:
                    players.append(
                        player
                    )


            ages=[
                p.age
                for p in players
                if p.age
            ]


            teams.append(
                {
                    "owner_id": roster.owner_id,

                    "player_count":len(players),

                    "ktc_value":sum(
                        p.ktc_value or 0
                        for p in players
                    ),

                    "fc_value":sum(
                        p.fc_value or 0
                        for p in players
                    ),

                    "starter_war":sum(
                        p.starter_war or 0
                        for p in players
                    ),

                    "roster_war":sum(
                        p.roster_war or 0
                        for p in players
                    ),

                    "average_age":(
                        mean(ages)
                        if ages
                        else None
                    ),
                }
            )


        rank_league_teams(
            teams
        )


        mine = next(
            x
            for x in teams
            if x["owner_id"] == user_id
        )


        output.append(
            {
                "league_id":league_id,
                "league_name":data["league"].name,

                "league_size":len(teams),

                "ktc_value":mine["ktc_value"],
                "ktc_rank":mine["ktc_rank"],

                "fc_value":mine["fc_value"],
                "fc_rank":mine["fc_rank"],

                "starter_war":mine["starter_war"],
                "starter_war_rank":mine["starter_war_rank"],

                "roster_war":mine["roster_war"],
                "roster_war_rank":mine["roster_war_rank"],

                "average_age":mine["average_age"],
                "age_rank":mine["age_rank"],
            }
        )


    return output