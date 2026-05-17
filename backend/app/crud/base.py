from sqlmodel import Session
import logging

from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session

logger = logging.getLogger(__name__)

def _bulk_upsert(db: Session, model, mappings: list[dict], index_elements: any):
    if not mappings:
        return

    model_columns = set(model.__table__.columns.keys())

    sanitized_mappings = [
        {k: v for k, v in m.items() if k in model_columns}
        for m in mappings
    ]

    stmt = insert(model).values(sanitized_mappings)

    if not isinstance(index_elements, list):
        index_elements = [index_elements]

    update_dict = {
        col: stmt.excluded[col]
        for col in sanitized_mappings[0].keys()
        if col not in index_elements
    }

    stmt = stmt.on_conflict_do_update(
        index_elements=index_elements,
        set_=update_dict
    )

    db.exec(stmt)