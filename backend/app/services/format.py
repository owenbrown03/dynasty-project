def format_players(player_ids: list[str], player_map: dict[str, dict]) -> list[str]:
    """
    Takes a pre-loaded player map and a list of IDs, filtering and sorting
    them into a position-prioritized text manifest.
    """
    pos_order = {"QB": 0, "RB": 1, "WR": 2, "TE": 3, "K": 4, "DEF": 5}    
    
    current_roster_dicts = [
        player_map[p_id] for p_id in player_ids 
        if p_id in player_map
    ]
    
    current_roster_dicts.sort(
        key=lambda p: (pos_order.get(p.get("position"), 99), p.get("last_name", ""))
    )
    
    return [
        f"{p.get('position')} {p.get('first_name')} {p.get('last_name')}" 
        for p in current_roster_dicts
    ]