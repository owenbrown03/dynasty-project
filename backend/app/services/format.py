from sqlmodel import Session

from app.crud.player import get_player_map

def format_players(db: Session, player_ids):
    player_map = get_player_map(db)
    pos_order = {"QB": 0, "RB": 1, "WR": 2, "TE": 3, "K": 4, "DEF": 5}    
    
    current_roster_dicts = [
        player_map[p_id] for p_id in player_ids 
        if p_id in player_map
    ]
    
    current_roster_dicts.sort(
        key=lambda p: (pos_order.get(p.get("position"), 99), p.get("last_name", ""))
    )
    
    formatted_players = [
        f"{p.get('position')} {p.get('first_name')} {p.get('last_name')}" 
        for p in current_roster_dicts
    ]
        
    return formatted_players