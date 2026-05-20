import logging, asyncio
from fastapi import HTTPException, status
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import models
from app.schemas import schemas
from app.services import sleeper
from app.crud.league import sync_leagues

logger = logging.getLogger(__name__)

async def user_id_lookup(db: AsyncSession, username: str) -> str:
    """
    Looks up the user ID locally first to completely bypass the network semaphore.
    Falls back to the network ONLY if it's a completely new user profile signature.
    """
    clean_username = username.strip()
    result = await db.execute(select(models.User.user_id).where(models.User.display_name == clean_username))
    user_id = result.scalar_one_or_none()
    
    if not user_id:
        username_details = await sleeper.get_username_details(clean_username)
        if not username_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{clean_username}' could not be resolved."
            )
        return username_details['user_id']
        
    return user_id

async def get_user_meta_map(db: AsyncSession) -> dict[str, dict]:
    """Returns a dict of {user_id: {"name": display_name, "avatar": avatar}}"""
    result = await db.execute(
        select(models.User.user_id, models.User.display_name, models.User.avatar)
    )
    rows = result.all()

    return {
        user_id: {"name": display_name, "avatar": avatar}
        for user_id, display_name, avatar in rows
    }

async def sync_user_data(db: AsyncSession, username: str) -> dict:

    user_id = await user_id_lookup(db, username)
    state = await sleeper.get_NFL_state()
    season = schemas.NFLState(**state).season
    leagues_json = await sleeper.get_leagues(user_id, season)
    
    if not leagues_json:
        return {"status": "skipped", "reason": "no_leagues"}
    else:    
        return await sync_leagues(db, leagues_json)