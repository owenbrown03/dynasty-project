from sqlalchemy import select, inspect
from sqlalchemy.orm import Session
import models, logging

logger = logging.getLogger(__name__)

def read_all(db: Session, *columns, **filters):
    query = db.query(*columns)
    if filters:
        query = query.filter_by(**filters)
    results = query.all()
    if not results:
        return set()
    if len(columns) == 1 and isinstance(columns[0], type):
        return results
    if len(columns) == 1:
        return {row[0] for row in results}
    else:
        return {tuple(row) for row in results}

def get_leaguemates(db: Session, main_user_id: str):
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