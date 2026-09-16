from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

import logging

logger = logging.getLogger(__name__)


def _normalize_bulk_mappings(
    model,
    mappings: list[dict],
) -> list[dict]:
    model_cols = set(model.__table__.columns.keys())

    clean = [
        {
            k: v
            for k, v in mapping.items()
            if k in model_cols
        }
        for mapping in mappings
    ]

    clean = [
        mapping
        for mapping in clean
        if mapping
    ]

    if not clean:
        return []

    all_keys = sorted(
        {
            key
            for mapping in clean
            for key in mapping.keys()
        }
    )

    return [
        {
            key: mapping.get(key)
            for key in all_keys
        }
        for mapping in clean
    ]


async def _bulk_upsert(
    db: AsyncSession,
    model,
    mappings: list[dict],
    index_elements: Any,
):

    if not mappings:
        return

    clean = _normalize_bulk_mappings(
        model,
        mappings,
    )

    if not clean:
        return

    conflict_cols = (
        [index_elements]
        if isinstance(index_elements, str)
        else list(index_elements)
    )
    conflict_set = set(conflict_cols)

    stmt = insert(model).values(clean)

    update = {
        k: stmt.excluded[k]
        for k in clean[0].keys()
        if k not in conflict_set
    }

    if not update:
        return

    stmt = stmt.on_conflict_do_update(
        index_elements=conflict_cols,
        set_=update
    )

    await db.execute(stmt)
