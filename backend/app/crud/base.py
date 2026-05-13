from sqlalchemy import insert, select
from sqlalchemy.orm import Session
import logging

from app.models import models

logger = logging.getLogger(__name__)

def _bulk_upsert(db: Session, model, data_list: list, index_elements):
    if not data_list:
        return
    seen = set()
    unique_data = []
    for d in data_list:
        key = tuple(d[k] for k in ([index_elements] if isinstance(index_elements, str) else index_elements))
        if key not in seen:
            unique_data.append(d)
            seen.add(key)

    stmt = insert(model).values(unique_data)
    stmt = stmt.on_conflict_do_update(index_elements=index_elements if isinstance(index_elements, list) else [index_elements])
    db.execute(stmt)

def get_league_map(db: Session) -> dict[str, str]:
    """Returns a dict of {league_id: league_name}"""
    result = db.execute(select(models.League.league_id, models.League.name)).all()
    return {l.league_id: l.name for l in result}

def get_user_meta_map(db: Session) -> dict[str, dict]:
    """Returns a dict of {user_id: {"name": display_name, "avatar": avatar}}"""
    result = db.execute(
        select(models.User.user_id, models.User.display_name, models.User.avatar)
    ).all()
    return {
        u.user_id: {"name": u.display_name, "avatar": u.avatar} 
        for u in result
    }

def get_leaguemates(db: Session, main_user_id: str):
    """Returns list[str]: A list of unique owner_ids (Sleeper IDs)."""
    my_leagues = (
        select(models.Roster.league_id)
        .where(models.Roster.owner_id == main_user_id)
        .scalar_subquery()
    )

    stmt = (
        select(models.Roster.owner_id)
        .where(
            models.Roster.league_id.in_(my_leagues),
            models.Roster.owner_id != main_user_id,
            models.Roster.owner_id.is_not(None)
        )
        .distinct()
    )

    return db.execute(stmt).scalars().all()