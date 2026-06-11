import logging
from typing import Any
from datetime import datetime, timedelta
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.models.sleeper import api as model
from app.schemas.sleeper import api as schema
from app.integrations.sleeper.client import SleeperClient
from app.services.sleeper import transformers 

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

async def sync_players(db: AsyncSession, sleeper: SleeperClient, force_update: bool = False):
    global _PLAYER_MAP_CACHE
    
    result = await db.execute(select(model.InternalState).where(model.InternalState.key == "last_player_map_update"))
    state = result.scalars().first()
    
    last_update = datetime.fromisoformat(state.value) if state and state.value else None
    if not force_update and last_update and last_update > (datetime.now() - timedelta(days=30)):
        return

    logger.info("Starting full Sleeper player sync...")

    players_map = await sleeper.read.get_all_players()
    
    player_dicts = transformers.player_to_db(players_map, return_dict=True)

    if player_dicts:
        chunk_size = 2000
        for i in range(0, len(player_dicts), chunk_size):
            chunk = player_dicts[i : i + chunk_size]
            
            stmt = insert(model.Player).values(chunk)
            stmt = stmt.on_conflict_do_update(
                index_elements=['player_id'],
                set_={k: getattr(stmt.excluded, k) for k in chunk[0].keys() if k != 'player_id'}
            )
            await db.execute(stmt)

    if not state:
        state = model.InternalState(key="last_player_map_update")
        db.add(state)
    state.value = datetime.now().isoformat()
    
    await db.commit()
    _PLAYER_MAP_CACHE.clear()
    logger.info(f"Player Sync Complete: Processed {len(player_dicts)} players.")