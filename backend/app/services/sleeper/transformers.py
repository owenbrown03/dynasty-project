from typing import Any
from app.schemas.sleeper import api as schema
from app.models.sleeper import api as model

def user_to_db(schema: schema.User, return_dict: bool = False) -> model.User | dict[str, Any]:
    """Transforms a nested Sleeper User payload into a flat User database entry."""
    data_map = schema.model_dump()
    
    if return_dict:
        return data_map
    return model.User(**data_map)

def player_to_db(schema: schema.Player, return_dict: bool = False) -> model.Player | dict[str, Any]:
    """Transforms a raw Sleeper Player payload into a flat database entity or raw dictionary."""
    data_map = schema.model_dump()
    
    if return_dict:
        return data_map
    return model.Player(**data_map)

def league_to_db(schema: schema.League, return_dict: bool = False) -> model.League | dict[str, Any]:
    """Transforms a nested Sleeper API payload into a flat League database entity safely."""
    full_data = schema.model_dump()
    
    settings = full_data.pop('settings', None) or {}
    scoring = full_data.pop('scoring_settings', None) or {}
    
    data_map = {
        **full_data,
        **settings,
        **scoring,
        "dynasty": settings.get('type') == 2,
        "roster_positions": full_data.get('roster_positions') or [],
        "bonus_rec_te": scoring.get("bonus_rec_te", 0),
        "rec": scoring.get("rec", 0),
        "pass_td": scoring.get("pass_td", 0),
        "best_ball": settings.get("best_ball", False),
    }
    
    if return_dict:
        return data_map
    return model.League(**data_map)

def roster_to_db(schema: schema.Roster, return_dict: bool = False) -> model.Roster | dict[str, Any]:
    """Transforms a nested Sleeper Roster schema into a flat database entity or raw dictionary."""
    data_map = schema.model_dump(exclude={'id'}) # Just keep the original map
    if "players" not in data_map or not data_map["players"]:
        data_map["players"] = []
        
    if return_dict:
        return data_map
    return model.Roster(**data_map)

def tx_to_db(
    schema: schema.Transaction, 
    league_id: str,
    return_dict: bool = False
) -> tuple[Any, list[Any], list[Any], list[Any]]:
    """Transforms a multi-entity transaction payload into database objects or raw dictionaries."""
    tx_data = {
        "transaction_id": schema.transaction_id,
        "type": schema.type,
        "time_ms": schema.status_updated,
        "league_id": league_id
    }

    movements_data = [
        {"transaction_id": schema.transaction_id, "player_id": p_id, "roster_id": r_id, "action": "ADD"}
        for p_id, r_id in (schema.adds or {}).items()
    ] + [
        {"transaction_id": schema.transaction_id, "player_id": p_id, "roster_id": r_id, "action": "DROP"}
        for p_id, r_id in (schema.drops or {}).items()
    ]

    waivers_data = [
        {"transaction_id": schema.transaction_id, "sender": w.sender, "receiver": w.receiver, "amount": w.amount}
        for w in (schema.waiver_budget or [])
    ]

    picks_data = [
        {
            "transaction_id": schema.transaction_id,
            "season": p.season,
            "round": p.round,
            "new_roster_id": p.owner_id,
            "old_roster_id": p.previous_owner_id,
            "og_roster_id": p.roster_id
        }
        for p in (schema.draft_picks or [])
    ]

    if return_dict:
        return tx_data, movements_data, waivers_data, picks_data
        
    return (
        model.Transaction(**tx_data),
        [model.Movement(**m) for m in movements_data],
        [model.WaiverBudget(**w) for w in waivers_data],
        [model.TradedPick(**p) for p in picks_data]
    )