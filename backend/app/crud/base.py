from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

import logging

logger = logging.getLogger(__name__)

async def _bulk_upsert(db: AsyncSession, model, mappings: list[dict], index_elements: Any):

    if not mappings:
        return

    model_cols = set(model.__table__.columns.keys())

    clean = [
        {k: v for k, v in m.items() if k in model_cols}
        for m in mappings
    ]

    if not clean:
        return

    conflict = (
        {index_elements}
        if not isinstance(index_elements, list)
        else set(index_elements)
    )

    stmt = insert(model).values(clean)

    update = {
        k: stmt.excluded[k]
        for k in clean[0].keys()
        if k not in conflict
    }

    if not update:
        return

    stmt = stmt.on_conflict_do_update(
        index_elements=list(conflict),
        set_=update
    )

    await db.execute(stmt)