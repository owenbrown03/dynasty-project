from sqlmodel import Session, select
import logging

from app.models import models
from app.services.format import format_players

logger = logging.getLogger(__name__)

async def get_user_rosters(db: Session, user_id: str) -> list[dict]:
    """
    Fetches all leagues an owner belongs to, unrolls their rostered player lists, 
    and returns a position-sorted manifest.
    """
    stmt = (
        select(models.League.name, models.Roster.players)
        .join(models.League, models.Roster.league_id == models.League.league_id)
        .where(models.Roster.owner_id == user_id)
    )
    raw_results = db.exec(stmt).all()
    
    formatted_rosters = []
    for league_name, player_ids in raw_results:
        formatted_players = format_players(db, player_ids)
        formatted_rosters.append({
            "league_name": league_name,
            "players": formatted_players
        })

    return formatted_rosters

async def get_user_orphans(db: Session, user_id: str) -> list[dict]:
    """
    Fetches all orphaned rosters in league of a specific user, 
    and returns a position-sorted manifest.
    """

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

    raw_results = db.exec(stmt).all()

    formatted_rosters = []
    for league_name, roster_id, player_ids in raw_results:
        formatted_players = format_players(db, player_ids)
        formatted_rosters.append({
            "league_name": league_name,
            "roster_name": "Team " + str(roster_id),
            "players": formatted_players
        })

    return formatted_rosters