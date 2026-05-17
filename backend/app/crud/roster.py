from sqlmodel import Session, select
import logging

from app.models import models
from app.crud.player import get_player_map

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

    player_map = get_player_map(db)
    pos_order = {"QB": 0, "RB": 1, "WR": 2, "TE": 3, "K": 4, "DEF": 5}
    formatted_rosters = []
    
    for league_name, player_ids in raw_results:
        id_list = player_ids or []
        
        current_roster_dicts = [
            player_map[p_id] for p_id in id_list 
            if p_id in player_map
        ]
        
        current_roster_dicts.sort(
            key=lambda p: (pos_order.get(p.get("position"), 99), p.get("last_name", ""))
        )
        
        names = [
            f"{p.get('position')} {p.get('first_name')} {p.get('last_name')}" 
            for p in current_roster_dicts
        ]
        
        formatted_rosters.append({
            "league_name": league_name,
            "players": names
        })
        
    return formatted_rosters