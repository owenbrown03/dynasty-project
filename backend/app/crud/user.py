import logging
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import models
from app.schemas import schemas
from app.services import sleeper
from app.crud.league import sync_leagues

logger = logging.getLogger(__name__)

async def get_user_meta_map(db: AsyncSession) -> dict[str, dict]:
    """Returns a dict of {user_id: {"name": display_name, "avatar": avatar}}"""
    result = await db.execute(
        select(models.User.user_id, models.User.display_name, models.User.avatar)
    ).all()

    return {
        user_id: {"name": display_name, "avatar": avatar}
        for user_id, display_name, avatar in result
    }

async def sync_user_data(db: AsyncSession, user_id: str) -> dict:
    logger.info(f"Executing single user sync for {user_id}...")
    
    state = await sleeper.get_NFL_state()
    season = schemas.NFLState(**state).season
    leagues_json = await sleeper.get_leagues(user_id, season)
    if not leagues_json:
        return {"status": "skipped", "reason": "no_leagues"}
        
    return await sync_leagues(db, leagues_json)