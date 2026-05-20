import logging, asyncio
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import sleeper
from app.schemas import schemas
from app.models import models
from app.crud.league import sync_leagues
from app.crud.user import user_id_lookup

logger = logging.getLogger(__name__)

async def get_leaguemate_ids(db: AsyncSession, username: str):
    """Returns list[str]: A list of unique owner_ids (Sleeper IDs)."""
    main_user_id = await user_id_lookup(db, username)
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

    result = await db.execute(stmt)
    return result.scalars().all()

async def sync_leaguemates(db: AsyncSession, username: str) -> dict:
    """
    Orchestrates discovery and synchronization of leagues belonging to all leaguemates.
    Optimized to minimize database connection hold-times during massive network I/O operations.
    """
    state = await sleeper.get_NFL_state()
    season = schemas.NFLState(**state).season

    try:
        main_user_id = await user_id_lookup(db, username)
        logger.info(f"Starting master leaguemate sync discovery workflow for user: {username}")
        lm_ids = await get_leaguemate_ids(db, main_user_id)
    except Exception as e:
        logger.error(f"Failed to retrieve leaguemate IDs from local schema: {str(e)}")
        raise e

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

    if not all_discovered_leagues:
        return {"status": "skipped", "reason": "no_leagues"}
    else:    
        return await sync_leagues(db, all_discovered_leagues)