import asyncio, logging
from sqlalchemy.orm import Session

from app.crud.base import get_leaguemates
from app.crud.user import create_user_data

logger = logging.getLogger(__name__)

async def leaguemate_sync(db: Session, main_user_id: str, season: str):
    lms = get_leaguemates(db, main_user_id)
    if not lms:
        logger.info("No leaguemates found to sync.")
        return
    logger.info(f"Syncing {len(lms)} leaguemates...")

    tasks = [create_user_data(db, lm_id, season) for lm_id in lms]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            logger.error(f"Error syncing leaguemate {lms[i]}: {res}")

    logger.info("Leaguemate sync cycle complete.")