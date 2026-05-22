import logging
from typing import Any
from datetime import datetime, timedelta
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.models import sleeper as model
from app.schemas import sleeper as schema
from app.services import sleeper, transformers 

logger = logging.getLogger(__name__)

_PLAYER_MAP_CACHE: dict[str, dict[str, Any]] = {}

async def get_player_map(db: AsyncSession) -> dict[str, dict[str, Any]]:
    """Fetches all players and caches them as plain dictionaries without DB session leaks."""
    global _PLAYER_MAP_CACHE
    
    if _PLAYER_MAP_CACHE:
        return _PLAYER_MAP_CACHE

    result = await db.execute(select(model.Player))
    players = result.scalars().all()
    
    _PLAYER_MAP_CACHE = {p.player_id: p.model_dump() for p in players}
    return _PLAYER_MAP_CACHE

async def sync_players(db: AsyncSession, force_update: bool = False):
    global _PLAYER_MAP_CACHE
    
    stmt = select(model.InternalState).where(model.InternalState.key == "last_player_map_update")
    
    result = await db.execute(stmt)
    state = result.scalars().first()
    
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
        p_schema = schema.Player.model_validate(p_json)
        
        p_dict = transformers.player_to_db(p_schema, return_dict=True)
        player_dicts.append(p_dict)

    if player_dicts:
        chunk_size = 2000
        for i in range(0, len(player_dicts), chunk_size):
            chunk = player_dicts[i : i + chunk_size]
            
            stmt = insert(model.Player).values(chunk)
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
            await db.execute(stmt)

    if not state:
        state = model.InternalState(key="last_player_map_update")
        db.add(state)
    
    state.value = datetime.now().isoformat()
    await db.commit()
    
    _PLAYER_MAP_CACHE.clear()
    
    logger.info(f"Player Sync Complete: Processed {len(player_dicts)} players. Cache cleared.")