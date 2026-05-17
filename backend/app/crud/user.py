import logging
from sqlmodel import Session, select

from app.models import models
from app.services import sleeper
from app.crud.league import sync_new_leagues

logger = logging.getLogger(__name__)

def get_user_meta_map(db: Session) -> dict[str, dict]:
    """Returns a dict of {user_id: {"name": display_name, "avatar": avatar}}"""
    result = db.exec(
        select(models.User.user_id, models.User.display_name, models.User.avatar)
    ).all()

    return {
        user_id: {"name": display_name, "avatar": avatar}
        for user_id, display_name, avatar in result
    }

async def sync_user_data(db: Session, user_id: str, season: str) -> dict:
    logger.info(f"Executing single user sync for {user_id}...")
    
    leagues_json = await sleeper.get_leagues(user_id, season)
    if not leagues_json:
        return {"status": "skipped", "reason": "no_leagues"}
        
    return await sync_new_leagues(db, leagues_json)