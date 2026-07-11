from __future__ import annotations

from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.db.ktc.models import KTCPickValue


async def get_ktc_pick_values(
    db: AsyncSession,
    *,
    seasons: list[str],
    rounds: list[int],
) -> dict[tuple[str, int], list[KTCPickValue]]:
    if not seasons or not rounds:
        return {}

    result = await db.execute(
        select(KTCPickValue)
        .where(
            KTCPickValue.season.in_(seasons),
            KTCPickValue.round.in_(rounds),
        )
        .order_by(
            KTCPickValue.season,
            KTCPickValue.round,
            KTCPickValue.bucket,
        )
    )

    output: dict[tuple[str, int], list[KTCPickValue]] = defaultdict(list)

    for row in result.scalars().all():
        output[(row.season, row.round)].append(row)

    return dict(output)
