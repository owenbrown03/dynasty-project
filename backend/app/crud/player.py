import logging
from typing import Any
from datetime import datetime, timedelta
from sqlmodel import Session, select
from sqlalchemy.dialects.postgresql import insert
from functools import lru_cache

from app.models import models 
from app.schemas import schemas
from app.services import sleeper, transformers 

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_player_map(db: Session) -> dict[str, dict[str, Any]]:
    """Fetches all players and caches them as plain dictionaries without DB session leaks."""
    players = db.exec(select(models.Player)).all()
    return {p.player_id: p.model_dump() for p in players}

async def sync_players(db: Session, force_update: bool = False):
    state_statement = select(models.InternalState).where(models.InternalState.key == "last_player_map_update")
    state = db.exec(state_statement).first()
    
    last_update = datetime.fromisoformat(state.value) if state else None
    threshold = datetime.now() - timedelta(days=30)
    
    if not force_update and last_update and last_update > threshold:
        logger.info(f"Player map is current (Last updated: {last_update.date()})")
        return

    logger.info("Starting full Sleeper player sync...")
    
    players_json = await sleeper.get_all_players()
    
    player_dicts = []
    for p_json in players_json.values():
        if not p_json:
            continue
        p_schema = schemas.SleeperPlayer.model_validate(p_json)
        
        p_dict = transformers.player_to_db(p_schema, return_dict=True)
        player_dicts.append(p_dict)

    if player_dicts:
        chunk_size = 2000
        for i in range(0, len(player_dicts), chunk_size):
            chunk = player_dicts[i : i + chunk_size]
            
            stmt = insert(models.Player).values(chunk)
            stmt = stmt.on_conflict_do_update(
                index_elements=['player_id'],
                set_={
                    "position": stmt.excluded.position,
                    "team": stmt.excluded.team,
                    "first_name": stmt.excluded.first_name,
                    "last_name": stmt.excluded.last_name,
                    "years_exp": stmt.excluded.years_exp,
                    "birth_date": stmt.excluded.birth_date
                }
            )
            db.exec(stmt)

    if not state:
        state = models.InternalState(key="last_player_map_update")
        db.add(state)
    
    state.value = datetime.now().isoformat()
    db.commit()
    
    get_player_map.cache_clear()
    
    logger.info(f"Player Sync Complete: Processed {len(player_dicts)} players. LRU cache cleared.")