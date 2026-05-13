from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import models
from app.crud.player import get_player_map

async def get_user_rosters(db: Session, user_id: str):    
    stmt = (
        select(models.League.name, models.Roster.players)
        .join(models.League, models.Roster.league_id == models.League.league_id)
        .where(models.Roster.owner_id == user_id)
    )
    raw_results = db.execute(stmt).all()

    player_map = get_player_map(db)
    pos_order = {"QB": 0, "RB": 1, "WR": 2, "TE": 3, "K": 4, "DEF": 5}
    formatted_rosters = []
    for league_name, player_ids in raw_results:
        id_list = player_ids or []
        current_roster_objects = [player_map[pid] for pid in id_list if pid in player_map]
        current_roster_objects.sort(key=lambda p: (pos_order.get(p.position, 99), p.last_name))
        
        names = [
            f"{p.position} {p.first_name} {p.last_name}" 
            for p in current_roster_objects
        ]
        
        formatted_rosters.append({
            "league_name": league_name,
            "players": names
        })
        
    return formatted_rosters