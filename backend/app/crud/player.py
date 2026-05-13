import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from functools import lru_cache

from app.models import models
from app.schemas import schemas
from app.services import mappers, sleeper

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_player_map(db: Session):
    players = db.query(models.Player).all()
    return {p.player_id: p for p in players}

async def sync_players(db: Session, force_update: bool = False):
    state = db.query(models.InternalState).filter_by(key="last_player_map_update").first()
    last_update = datetime.fromisoformat(state.value) if state else None
    
    threshold = datetime.now() - timedelta(days=30)
    
    if not force_update and last_update and last_update > threshold:
        logger.info(f"Player map is current (Last updated: {last_update.date()})")
        return

    logger.info("Starting full Sleeper player sync...")
    
    players_json = await sleeper.get_all_players()
    
    player_dicts = []
    for p_json in players_json.values():
        p_schema = schemas.SleeperPlayer(**p_json)
        player_dicts.append(mappers.schema_to_db(p_schema))

    if player_dicts:
        chunk_size = 2000
        for i in range(0, len(player_dicts), chunk_size):
            chunk = player_dicts[i : i + chunk_size]
            
            stmt = insert(models.Player).values(chunk)
            
            stmt = stmt.on_conflict_do_update(
                index_elements=['player_id'],
                set_={
                    "team": stmt.excluded.team,
                    "birth_date": stmt.excluded.birth_date
                }
            )
            db.execute(stmt)

    if not state:
        state = models.InternalState(key="last_player_map_update")
        db.add(state)
    
    state.value = datetime.now().isoformat()
    db.commit()
    
    logger.info(f"Player Sync Complete: Processed {len(player_dicts)} players.")