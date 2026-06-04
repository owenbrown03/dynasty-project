import logging, asyncio
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.sleeper.client import SleeperClient
from app.models.sleeper import api as model
from app.crud.sleeper.league import sync_leagues
from app.crud.sleeper.user import get_userid_by_username

logger = logging.getLogger(__name__)

async def get_leaguemate_ids(db: AsyncSession, username: str, sleeper: SleeperClient):
    """Returns list[str]: A list of unique owner_ids (Sleeper IDs)."""
    main_user_id = await get_userid_by_username(db, username, sleeper)
    my_leagues = (
        select(model.Roster.league_id)
        .where(model.Roster.owner_id == main_user_id)
        .scalar_subquery()
    )

    stmt = (
        select(model.Roster.owner_id)
        .where(
            model.Roster.league_id.in_(my_leagues),
            model.Roster.owner_id != main_user_id,
            model.Roster.owner_id.is_not(None)
        )
        .distinct()
    )

    result = await db.execute(stmt)
    return result.scalars().all()

async def sync_leaguemates(db: AsyncSession, username: str, sleeper: SleeperClient) -> dict:
    """
    Orchestrates discovery and synchronization of leagues belonging to all leaguemates.
    Optimized to minimize database connection hold-times during massive network I/O operations.
    """
    state = await sleeper.read.get_nfl_state()
    season = state["season"]
    curr_week = state["week"]
    try:
        main_user_id = await get_userid_by_username(db, username, sleeper)
        logger.info(f"Starting master leaguemate sync discovery workflow for user: {username}")
        lm_ids = await get_leaguemate_ids(db, main_user_id, sleeper)
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
            return await sleeper.read.get_leagues(lm_id, season)
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
        return await sync_leagues(db, all_discovered_leagues, curr_week, sleeper)