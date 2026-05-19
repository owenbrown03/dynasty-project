from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

import logging

logger = logging.getLogger(__name__)

async def _bulk_upsert(db: AsyncSession, model, mappings: list[dict], index_elements: any):
    if not mappings:
        return

    model_columns = set(model.__table__.columns.keys())

    sanitized_mappings = [
        {k: v for k, v in m.items() if k in model_columns}
        for m in mappings
    ]

    if not isinstance(index_elements, list):
        conflict_keys = {index_elements}
    else:
        conflict_keys = set(index_elements)

    stmt = insert(model).values(sanitized_mappings)

    update_dict = {
        col: stmt.excluded[col]
        for col in sanitized_mappings[0].keys()
        if col not in conflict_keys
    }

    stmt = stmt.on_conflict_do_update(
        index_elements=list(conflict_keys),
        set_=update_dict
    )

    await db.execute(stmt)