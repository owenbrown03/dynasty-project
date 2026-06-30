from app.crud.sleeper.league import get_league_context

class LeagueAnalyzer:

    async def load(
        self,
        db,
        league_id,
    ):
        context = await get_league_context(
            db,
            league_id,
        )

        return context