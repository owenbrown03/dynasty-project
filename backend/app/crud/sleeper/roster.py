from fastapi import HTTPException, status
from collections import defaultdict
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.sleeper.client import SleeperClient
from app.models.db.sleeper.api import League, Roster
from app.models.db.sleeper.connection import SleeperConnection
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
        select(League.name, Roster.players)
        .join(League, Roster.league_id == League.league_id)
        .where(Roster.owner_id == user_id)
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
        select(Roster.league_id)
        .where(Roster.owner_id == user_id)
        .scalar_subquery()
    )

    stmt = (
        select(League.name, Roster.roster_id, Roster.players)
        .join(League, Roster.league_id == League.league_id)
        .where(Roster.league_id.in_(my_leagues), Roster.owner_id == None)
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


async def get_all_rosters_by_league(
    *,
    db: AsyncSession,
    league_ids: list[str],
) -> dict[str, list[Roster]]:
    """
    Returns all roster rows for all owned leagues in one query.
    """

    result = await db.execute(
        select(Roster).where(
            Roster.league_id.in_(
                league_ids,
            )
        )
    )

    rosters_by_league: dict[
        str,
        list[Roster],
    ] = defaultdict(list)

    for roster in result.scalars():
        rosters_by_league[
            roster.league_id
        ].append(
            roster,
        )

    return rosters_by_league

def get_target_owner_roster(
    *,
    target_player_id: str,
    league_rosters: list[Roster],
) -> Roster | None:
    """
    Returns the roster currently containing the selected player.

    A player should appear on at most one roster in one league.
    """

    return next(
        (
            roster
            for roster in league_rosters
            if target_player_id in (
                roster.players or []
            )
        ),
        None,
    )


async def get_owned_roster_rows(
    *,
    db: AsyncSession,
    connection: SleeperConnection,
) -> list[tuple[Roster, League]]:
    """
    Returns one roster/league pair for every league owned by the connected
    Sleeper account.
    """

    if not connection.sleeper_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Connected Sleeper account is missing a "
                "Sleeper user ID."
            ),
        )

    result = await db.execute(
        select(
            Roster,
            League,
        )
        .join(
            League,
            League.league_id == Roster.league_id,
        )
        .where(
            Roster.owner_id == connection.sleeper_user_id,
        )
        .order_by(
            League.name,
        )
    )

    return list(
        result.all(),
    )


async def get_owned_roster_rows(
    *,
    db: AsyncSession,
    connection: SleeperConnection,
) -> list[tuple[Roster, League]]:
    """
    Gets all roster/league pairs owned by the connected Sleeper account.
    """

    if not connection.sleeper_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Connected Sleeper account is missing "
                "a Sleeper user ID."
            ),
        )

    result = await db.execute(
        select(Roster, League)
        .join(
            League,
            League.league_id == Roster.league_id,
        )
        .where(
            Roster.owner_id == connection.sleeper_user_id,
        )
        .order_by(
            League.name,
        )
    )

    return list(
        result.all(),
    )
