from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.auth import SiteUser

async def insert_sleeper_id(sleeper_id: str, site_user_id: str, db: AsyncSession):
    result = await db.execute(select(SiteUser).where(SiteUser.id == site_user_id))
    user = result.scalar_one_or_none()
    if user:
        user.sleeper_id = sleeper_id
        await db.commit()
        await db.refresh(user)
        return {"message": "Sleeper id inserted"}
    else:
        return {"message": "User not in database"}
    
async def get_sleeper_id(site_user_id: str, db: AsyncSession):
    result = await db.execute(select(SiteUser).where(SiteUser.id == site_user_id))
    return result.scalar_one_or_none().sleeper_id