import logging
from typing import Any
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from sqlalchemy import func
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.models.db.sleeper.api import Player, InternalState, PlayerProjection
from app.integrations.sleeper.client import SleeperClient
from app.services.sleeper import transformers
from app.services.waivers.dynasty import DYNASTY_FANTASY_POSITIONS

logger = logging.getLogger(__name__)


_PLAYER_MAP_CACHE: dict[str, dict] | None = None

async def get_player_map(
    db,
) -> dict[str, dict]:
    global _PLAYER_MAP_CACHE

    if _PLAYER_MAP_CACHE is not None:
        return _PLAYER_MAP_CACHE

    result = await db.execute(
        select(
            Player,
        )
    )

    players = result.scalars().all()

    _PLAYER_MAP_CACHE = {
        player.player_id: player.model_dump()
        for player in players
    }

    return _PLAYER_MAP_CACHE


_PLAYER_SNAPSHOT_CACHE: dict[str, dict[str, Any]] = {}

async def get_analytics_player_map(db: AsyncSession,) -> dict[str, dict[str, Any]]:
    """Returns a lightweight immutable player snapshot for analytics calculations."""
    global _PLAYER_SNAPSHOT_CACHE

    if _PLAYER_SNAPSHOT_CACHE:
        return _PLAYER_SNAPSHOT_CACHE

    players = await get_player_map(db)

    _PLAYER_SNAPSHOT_CACHE = {
        player_id: {
            "player_id": player_id,
            "first_name": player.get("first_name"),
            "last_name": player.get("last_name"),
            "position": player.get("position"),
            "team": player.get("team"),
            "birth_date": player.get("birth_date"),
        }
        for player_id, player in players.items()
    }

    return _PLAYER_SNAPSHOT_CACHE


async def sync_players(db: AsyncSession, sleeper: SleeperClient, force_update: bool = False):
    global _PLAYER_MAP_CACHE
    
    result = await db.execute(select(InternalState).where(InternalState.key == "last_player_map_update"))
    state = result.scalars().first()
    
    last_update = datetime.fromisoformat(state.value) if state and state.value else None
    if not force_update and last_update and last_update > (datetime.now() - timedelta(days=30)):
        return

    logger.info("Starting full Sleeper player sync...")

    players_map = await sleeper.read.get_all_players() 
    
    player_dicts = [
        transformers.player_to_db(p_data, return_dict=True) 
        for p_data in players_map.values()
    ]

    if player_dicts:
        chunk_size = 2000
        for i in range(0, len(player_dicts), chunk_size):
            chunk = player_dicts[i : i + chunk_size]
            
            stmt = insert(Player).values(chunk)
            stmt = stmt.on_conflict_do_update(
                index_elements=['player_id'],
                set_={k: getattr(stmt.excluded, k) for k in chunk[0].keys() if k != 'player_id'}
            )
            await db.execute(stmt)

    if not state:
        state = InternalState(key="last_player_map_update")
        db.add(state)
    state.value = datetime.now().isoformat()
    
    await db.commit()
    _PLAYER_MAP_CACHE.clear()
    _PLAYER_SNAPSHOT_CACHE.clear()
    logger.info(f"Player Sync Complete: Processed {len(player_dicts)} players.")


async def get_bulk_target_player(
    *,
    db: AsyncSession,
    player_id: str,
) -> Player:
    result = await db.execute(
        select(Player).where(
            Player.player_id == player_id,
        )
    )

    player = result.scalar_one_or_none()

    if player is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player was not found.",
        )

    if player.position not in DYNASTY_FANTASY_POSITIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Bulk waiver claims currently support only "
                "QB, RB, WR, and TE players."
            ),
        )

    return player


async def get_supported_player_ids(
    db: AsyncSession,
) -> list[str]:
    result = await db.execute(
        select(Player.player_id)
        .where(
            Player.position.in_(
                DYNASTY_FANTASY_POSITIONS,
            )
        )
        .order_by(
            Player.player_id,
        )
    )

    return list(
        result.scalars().all(),
    )


async def get_latest_projection_season(
    db: AsyncSession,
) -> int | None:
    result = await db.execute(
        select(
            func.max(
                PlayerProjection.season,
            )
        )
    )

    return result.scalar_one_or_none()
