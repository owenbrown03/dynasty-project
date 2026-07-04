from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.war.redraft.singleton import war_service
from app.crud.sleeper.league import get_league_with_rosters
from app.crud.sleeper.user import get_users
from app.crud.value import get_player_values



class LeagueDetails:

    def __init__(self):
        self.war_service = war_service


    async def get_league_details(
        self,
        db: AsyncSession,
        redis,
        league_id: str,
    ):


        leagues = await get_league_with_rosters(
            db,
            league_id,
        )


        if not leagues:
            return None



        league = leagues[0][0]



        # ----------------------------------
        # WAR
        # ----------------------------------

        shared = await self.war_service.load_shared_data(
            db,
            int(league.season),
        )

        war_players = await self.war_service.calculate_with_data(
            league=league,
            shared=shared,
        )

        war_lookup = {
            p.player_id:p
            for p in war_players
        }


        # ----------------------------------
        # Players
        # ----------------------------------

        player_ids = set()


        owner_ids = set()


        for _, roster in leagues:

            player_ids.update(
                roster.players or []
            )


            if roster.owner_id:
                owner_ids.add(
                    roster.owner_id
                )



        users = await get_users(
            db,
            owner_ids,
        )



        players = await get_player_values(
            db,
            player_ids,
            war_players,
        )


        player_map = {
            p.player_id:p
            for p in players
        }



        # ----------------------------------
        # Build response
        # ----------------------------------

        rosters = []


        for _, roster in leagues:


            roster_players = []


            starter_total = 0
            roster_total = 0



            for player_id in roster.players or []:


                player = player_map.get(
                    player_id
                )


                if not player:
                    continue



                war = war_lookup.get(
                    player_id
                )


                starter_war = (
                    war.starter_war
                    if war
                    else None
                )


                roster_war = (
                    war.roster_war
                    if war
                    else None
                )


                if starter_war is not None:
                    starter_total += starter_war


                if roster_war is not None:
                    roster_total += roster_war



                roster_players.append(
                    {
                        "player_id": player.player_id,
                        "name": player.name,
                        "position": player.position,
                        "team": player.team,

                        "age": player.age,

                        "ktc_value": player.ktc_value,
                        "fc_value": player.fc_value,

                        "starter_war": starter_war,
                        "roster_war": roster_war,
                    }
                )



            owner = users.get(
                roster.owner_id
            )


            rosters.append(
                {
                    "roster_id": roster.roster_id,

                    "owner": {
                        "user_id": owner.user_id,
                        "display_name": owner.display_name,
                        "avatar": owner.avatar,
                    }
                    if owner
                    else None,


                    "total_starter_war": round(
                        starter_total,
                        3,
                    ),

                    "total_roster_war": round(
                        roster_total,
                        3,
                    ),

                    "players": roster_players,
                }
            )



        # ----------------------------------
        # Ranking
        # ----------------------------------

        rosters.sort(
            key=lambda x: x["total_roster_war"],
            reverse=True,
        )


        for rank, roster in enumerate(
            rosters,
            start=1,
        ):
            roster["rank"] = rank



        return {
            "league_id": league.league_id,
            "league_name": league.name,
            "rosters": rosters,
        }