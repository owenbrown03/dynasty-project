from sqlmodel import select

from app.models.db.sleeper.api import Player, League, PlayerProjection

class PlayerValueLoader:

    async def get_league(
        self,
        db,
        league_id,
    ):
        league = await db.get(
            League,
            league_id,
        )

        if not league:
            raise ValueError(
                f"League {league_id} not found"
            )

        return league


    async def get_projections(
        self,
        db,
        season,
    ):
        result = await db.execute(
            select(PlayerProjection)
            .where(
                PlayerProjection.season == season
            )
        )

        return result.scalars().all()


    async def get_players(
        self,
        db,
    ):
        result = await db.execute(
            select(Player)
        )

        return {
            p.player_id:p
            for p in result.scalars()
        }