from app.core.broker import broker
from app.core.database import AsyncSessionLocal
from app.crud.sleeper.user import sync_user_data

@broker.task
async def sync_user_data_task(
    username: str,
):
    sleeper = broker.state.sleeper
    async with AsyncSessionLocal() as db:
        result = await sync_user_data(
            db, 
            username, 
            sleeper,
        )
        await db.commit()
        return result