from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.sleeper.client import SleeperClient
from app.models.sleeper import api
from app.crud.sleeper.player import get_player_map
from app.services.sleeper.format import format_players
from app.crud.sleeper.user import get_userid_by_username

async def get_user_rosters(db: AsyncSession, sleeper: SleeperClient, username: str) -> list[dict]:
    """
    Fetches all leagues an owner belongs to, unrolls their rostered player lists, 
    and returns a position-sorted manifest.
    """
    user_id = await get_userid_by_username(db, sleeper, username)
    stmt = (
        select(api.League.name, api.Roster.players)
        .join(api.League, api.Roster.league_id == api.League.league_id)
        .where(api.Roster.owner_id == user_id)
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

async def get_user_orphans(db: AsyncSession, sleeper: SleeperClient, username: str) -> list[dict]:
    """
    Fetches all orphaned rosters in leagues of a specific user, 
    and returns a position-sorted manifest.
    """
    user_id = await get_userid_by_username(db, sleeper, username)
    my_leagues = (
        select(api.Roster.league_id)
        .where(api.Roster.owner_id == user_id)
        .scalar_subquery()
    )

    stmt = (
        select(api.League.name, api.Roster.roster_id, api.Roster.players)
        .join(api.League, api.Roster.league_id == api.League.league_id)
        .where(api.Roster.league_id.in_(my_leagues), api.Roster.owner_id == None)
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