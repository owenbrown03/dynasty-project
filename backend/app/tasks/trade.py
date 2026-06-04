from app.core.broker import broker
from app.core.database import AsyncSessionLocal
from app.crud.sleeper.leaguemate import sync_leaguemates


@broker.task
async def sync_leaguemates_task(
    username: str,
):
    sleeper = broker.state.sleeper
    async with AsyncSessionLocal() as db:
        result = await sync_leaguemates(
            db,
            username,
            sleeper,
        )
        await db.commit()
        return result