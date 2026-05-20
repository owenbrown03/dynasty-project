import logging
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import models
from app.crud.player import get_player_map
from app.services.format import format_players
from app.crud.user import user_id_lookup

logger = logging.getLogger(__name__)

async def get_user_rosters(db: AsyncSession, username: str) -> list[dict]:
    """
    Fetches all leagues an owner belongs to, unrolls their rostered player lists, 
    and returns a position-sorted manifest.
    """
    user_id = await user_id_lookup(db, username)
    stmt = (
        select(models.League.name, models.Roster.players)
        .join(models.League, models.Roster.league_id == models.League.league_id)
        .where(models.Roster.owner_id == user_id)
    )
    result = await db.execute(stmt)
    raw_results = result.all()
    
    player_map = await get_player_map(db)
    
    formatted_rosters = []
    for league_name, player_ids in raw_results:
        formatted_players = format_players(player_ids, player_map)
        formatted_rosters.append({
            "league_name": league_name,
            "players": formatted_players
        })

    return formatted_rosters

async def get_user_orphans(db: AsyncSession, username: str) -> list[dict]:
    """
    Fetches all orphaned rosters in leagues of a specific user, 
    and returns a position-sorted manifest.
    """
    user_id = await user_id_lookup(db, username)
    my_leagues = (
        select(models.Roster.league_id)
        .where(models.Roster.owner_id == user_id)
        .scalar_subquery()
    )

    stmt = (
        select(models.League.name, models.Roster.roster_id, models.Roster.players)
        .join(models.League, models.Roster.league_id == models.League.league_id)
        .where(models.Roster.league_id.in_(my_leagues), models.Roster.owner_id == None)
        .distinct()
    )

    result = await db.execute(stmt)
    raw_results = result.all()

    player_map = await get_player_map(db)

    formatted_rosters = []
    for league_name, roster_id, player_ids in raw_results:
        formatted_players = format_players(player_ids, player_map)
        formatted_rosters.append({
            "league_name": league_name,
            "roster_name": "Team " + str(roster_id),
            "players": formatted_players
        })

    return formatted_rosters