from app.core.database import AsyncSessionLocal
from app.crud.user import sync_user_data
from app.core.broker import broker

@broker.task
async def sync_user_data_task(username: str):
    async with AsyncSessionLocal() as db:
        result = await sync_user_data(db, username)
        await db.commit()
        return result