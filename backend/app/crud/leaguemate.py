import asyncio
import logging
from sqlmodel import Session, select

from app.core.database import engine
from app.services import sleeper
from app.models import models
from app.crud.league import sync_new_leagues

logger = logging.getLogger(__name__)

def get_leaguemate_ids(db: Session, main_user_id: str):
    """Returns list[str]: A list of unique owner_ids (Sleeper IDs)."""
    my_leagues = (
        select(models.Roster.league_id)
        .where(models.Roster.owner_id == main_user_id)
        .scalar_subquery()
    )

    stmt = (
        select(models.Roster.owner_id)
        .where(
            models.Roster.league_id.in_(my_leagues),
            models.Roster.owner_id != main_user_id,
            models.Roster.owner_id.is_not(None)
        )
        .distinct()
    )

    return db.exec(stmt).all()

async def sync_leaguemates(main_user_id: str, season: str) -> dict:
    """
    Orchestrates discovery and synchronization of leagues belonging to all leaguemates.
    Utilizes structured milestone logs for tracking high-concurrency API loops.
    """
    db = Session(engine)
    logger.info(f"Starting master leaguemate sync discovery workflow for user: {main_user_id}")
    
    try:
        lm_ids = get_leaguemate_ids(db, main_user_id)
        total_leaguemates = len(lm_ids)
        logger.info(f"Context verified: Identified {total_leaguemates} leaguemates to process.")

        if total_leaguemates == 0:
            logger.info("Sync discovery skipped: No leaguemates found.")
            return {"status": "skipped", "synced_count": 0}

        processed_lms = 0
        progress_interval = 10
        log_milestone = max(1, total_leaguemates // progress_interval)

        async def fetch_leagues_with_progress(lm_id):
            nonlocal processed_lms
            try:
                return await sleeper.get_leagues(lm_id, season)
            finally:
                processed_lms += 1
                if total_leaguemates >= progress_interval and processed_lms % log_milestone == 0:
                    logger.info(f"[Leaguemate Discovery] Discovered league rosters for {processed_lms}/{total_leaguemates} leaguemates.")

        api_tasks = [fetch_leagues_with_progress(lm_id) for lm_id in lm_ids]
        api_results = await asyncio.gather(*api_tasks, return_exceptions=True)

        all_discovered_leagues = []
        for res in api_results:
            if isinstance(res, list):
                all_discovered_leagues.extend(res)
            elif isinstance(res, Exception):
                logger.error(f"Suppressed network fault encountered during user discovery scan: {str(res)}")

        logger.info(f"Discovery phase complete: Scraped {len(all_discovered_leagues)} total league instances from network pools.")

        result = await sync_new_leagues(db, all_discovered_leagues)
        return result

    except Exception as e:
        logger.error(f"Critical execution block fault captured inside leaguemate manager: {str(e)}", exc_info=True)
        raise e
        
    finally:
        try:
            db.rollback()
        except Exception:
            pass
            
        db.close()
        logger.info("Database session cleanly closed and returned to pool.")