from app.core.broker import broker
from app.core.database import AsyncSessionLocal
from app.crud.sleeper.user import sync_user_data
from app.integrations.sleeper.singleton import get_worker_sleeper_client

@broker.task
async def sync_user_data_task(username: str):
    async with AsyncSessionLocal() as db:
        sleeper = get_worker_sleeper_client()

        result = await sync_user_data(
            db,
            sleeper,
            username,
        )

        await db.commit()
        return result