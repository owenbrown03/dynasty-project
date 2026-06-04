import logging
from fastapi import HTTPException, status
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sleeper import api as model
from app.integrations.sleeper.client import SleeperClient
from app.crud.sleeper.league import sync_leagues

logger = logging.getLogger(__name__)

async def get_userid_by_username(db: AsyncSession, username: str, sleeper: SleeperClient) -> str:
    """
    Looks up the user ID locally first to completely bypass the network semaphore.
    Falls back to the network ONLY if it's a completely new user profile signature.
    """
    clean_username = username.strip()
    result = await db.execute(select(model.User.user_id).where(model.User.display_name == clean_username))
    user_id = result.scalar_one_or_none()
    
    if not user_id:
        username_details = await sleeper.read.get_user_details_by_username(clean_username)
        if not username_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{clean_username}' could not be resolved."
            )
        return username_details['user_id']
        
    return user_id

async def get_username_by_userid(db: AsyncSession, user_id: str, sleeper: SleeperClient) -> str:
    """
    Looks up the user ID locally first to completely bypass the network semaphore.
    Falls back to the network ONLY if it's a completely new user profile signature.
    """
    result = await db.execute(select(model.User.display_name).where(model.User.user_id == user_id))
    username = result.scalar_one_or_none()
    if not username:
        user_id_details = await sleeper.read.get_user_details_by_username(user_id)
        if not user_id_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{user_id}' could not be resolved."
            )
        return user_id_details['display_name']
    return username

async def get_user_meta_map(db: AsyncSession) -> dict[str, dict]:
    """Returns a dict of {user_id: {"name": display_name, "avatar": avatar}}"""
    result = await db.execute(
        select(model.User.user_id, model.User.display_name, model.User.avatar)
    )
    rows = result.all()

    return {
        user_id: {"name": display_name, "avatar": avatar}
        for user_id, display_name, avatar in rows
    }

async def sync_user_data(db: AsyncSession, username: str, sleeper: SleeperClient) -> dict:
    user_id = await user_id_lookup(db, username, sleeper)
    state = await sleeper.read.get_nfl_state()
    season = state["season"]
    curr_week = state["week"]
    leagues_json = await sleeper.read.get_leagues(user_id, season)
    
    if not leagues_json:
        return {"status": "skipped", "reason": "no_leagues"}
    else:    
        return await sync_leagues(db, leagues_json, curr_week, sleeper)