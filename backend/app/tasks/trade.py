from app.core.broker import broker
from app.core.database import AsyncSessionLocal
from app.crud.sleeper.leaguemate import sync_leaguemates
from app.integrations.sleeper.singleton import get_worker_sleeper_client
    
@broker.task
async def sync_leaguemates_task(username: str):
    async with AsyncSessionLocal() as db:
        sleeper = await get_worker_sleeper_client()

        result = await sync_leaguemates(
            db,
            sleeper,
            username,
        )

        await db.commit()
        return result