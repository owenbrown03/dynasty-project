import logging
from typing import Any
from app.integrations.sleeper.schemas import api as schema
from app.models.db.sleeper import api as model

logger = logging.getLogger(__name__)

def user_to_db(
    schema: schema.User,
    return_dict: bool = False
) -> model.User | dict[str, Any]:
    data_map = schema.model_dump()

    data_map.update({
        "is_placeholder": False,
        "is_owner": data_map.get("is_owner", False),
    })

    if return_dict:
        return data_map

    return model.User(**data_map)

def player_to_db(
    schema: schema.Player | dict,
    return_dict: bool = False,
) -> model.Player | dict[str, Any]:
    """Transforms a Sleeper player payload into a DB-safe player record."""

    raw = schema if isinstance(schema, dict) else schema.model_dump()

    data_map = {
        "player_id": raw.get("player_id"),
        "position": raw.get("position"),
        "team": raw.get("team"),
        "first_name": raw.get("first_name"),
        "last_name": raw.get("last_name"),
        "years_exp": raw.get("years_exp"),
        "birth_date": raw.get("birth_date"),
        "status": raw.get("status"),
        "injury_status": raw.get("injury_status"),
        "injury_body_part": raw.get("injury_body_part"),
        "active": raw.get("active", True),
    }

    if return_dict:
        return data_map

    return model.Player(**data_map)

def league_to_db(
    schema: schema.League,
    return_dict: bool = False,
) -> model.League | dict[str, Any]:
    """Transforms a Sleeper league payload into a DB-safe league record."""

    full_data = schema.model_dump()

    settings = full_data.get("settings") or {}
    scoring_settings = full_data.get("scoring_settings") or {}

    data_map = {
        "league_id": full_data["league_id"],
        "name": full_data["name"],
        "avatar": full_data.get("avatar"),
        "season": full_data["season"],
        "status": full_data.get("status") or "pre_draft",
        "total_rosters": full_data["total_rosters"],
        "draft_id": full_data["draft_id"],
        "previous_league_id": full_data.get("previous_league_id"),
        "league_metadata": full_data.get("metadata") or {},
        "settings": settings,
        "scoring_settings": scoring_settings,
        "roster_positions": full_data.get("roster_positions") or [],
    }

    if return_dict:
        return data_map

    return model.League(**data_map)

def roster_to_db(
    schema: schema.Roster,
    return_dict: bool = False,
) -> model.Roster | dict[str, Any]:
    """Transforms a Sleeper roster payload into a DB-safe roster record."""

    full_data = schema.model_dump()

    data_map = {
        "roster_id": full_data["roster_id"],
        "owner_id": full_data.get("owner_id"),
        "league_id": full_data["league_id"],
        "players": full_data.get("players") or [],
        "starters": full_data.get("starters") or [],
        "reserve": full_data.get("reserve") or [],
        "taxi": full_data.get("taxi") or [],
        "roster_metadata": full_data.get("metadata") or {},
        "settings": full_data.get("settings") or {},
    }

    if return_dict:
        return data_map

    return model.Roster(**data_map)

def draft_to_db(
    schema: schema.Draft,
    return_dict: bool = False,
) -> model.Draft | dict[str, Any]:
    """Transforms a Sleeper draft payload into a DB-safe draft record."""

    full_data = schema.model_dump()

    data_map = {
        "draft_id": full_data["draft_id"],
        "league_id": full_data["league_id"],
        "season": full_data["season"],
        "draft_order": full_data.get("draft_order") or {},
        "slot_to_roster_id": full_data.get("slot_to_roster_id") or {},
    }

    if return_dict:
        return data_map

    return model.Draft(**data_map)

def tx_to_db(
    schema: schema.Transaction, 
    league_id: str,
    return_dict: bool = False
) -> tuple[Any, list[Any], list[Any], list[Any]]:
    """Transforms a multi-entity transaction payload into database objects or raw dictionaries."""
    time_ms = getattr(
        schema,
        "status_updated",
        None,
    )

    if time_ms is None:
        time_ms = getattr(
            schema,
            "time",
            None,
        )

    if time_ms is None:
        raise ValueError(
            "Transaction payload missing status_updated/time timestamp."
        )

    tx_data = {
        "transaction_id": schema.transaction_id,
        "type": schema.type,
        "status": getattr(
            schema,
            "status",
            None,
        ),
        "time_ms": time_ms,
        "league_id": league_id,
    }

    movements_data = [
        {"transaction_id": schema.transaction_id, "player_id": p_id, "roster_id": r_id, "action": "ADD"}
        for p_id, r_id in (schema.adds or {}).items()
    ] + [
        {"transaction_id": schema.transaction_id, "player_id": p_id, "roster_id": r_id, "action": "DROP"}
        for p_id, r_id in (schema.drops or {}).items()
    ]

    waivers = schema.waiver_budget or []
    if isinstance(waivers, dict):
        waivers = []

    waivers_data = [
        {
            "transaction_id": schema.transaction_id,
            "sender": w.sender,
            "receiver": w.receiver,
            "amount": w.amount,
        }
        for w in waivers
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
