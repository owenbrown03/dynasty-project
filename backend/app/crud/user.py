import asyncio
import logging
from sqlalchemy.orm import Session
from app.models import models
from app.services import sleeper
from app.crud.league import get_league_data, sync_league_data

logger = logging.getLogger(__name__)

async def create_user_data(db: Session, user_id: str, season: str):
    leagues_json = await sleeper.get_leagues(user_id, season)
    if not leagues_json:
        logger.info(f"No leagues found for user {user_id} in season {season}")
        return

    all_incoming_ids = [l['league_id'] for l in leagues_json]

    existing_leagues = (
        db.query(models.League.league_id)
        .filter(models.League.league_id.in_(all_incoming_ids))
        .all()
    )
    existing_ids = {l[0] for l in existing_leagues}

    new_leagues = [l for l in leagues_json if l['league_id'] not in existing_ids]

    if not new_leagues:
        logger.info(f"All {len(leagues_json)} leagues for user {user_id} are already synced.")
        return

    logger.info(f"Found {len(new_leagues)} new leagues to sync for user {user_id}.")

    tasks = [get_league_data(l) for l in new_leagues]
    league_data_results = await asyncio.gather(*tasks)
    
    await sync_league_data(db, league_data_results)
    
    logger.info(f"Successfully synced data for {len(new_leagues)} new leagues.")