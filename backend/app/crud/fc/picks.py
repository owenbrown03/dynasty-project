from __future__ import annotations

from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.db.fc.models import FantasyCalcPickValue


async def get_fantasycalc_pick_values(
    db: AsyncSession,
    *,
    is_dynasty: bool,
    num_qbs: int,
    num_teams: int,
    ppr: int,
    seasons: list[str],
    rounds: list[int],
) -> dict[tuple[str, int], list[FantasyCalcPickValue]]:
    if not seasons or not rounds:
        return {}

    result = await db.execute(
        select(FantasyCalcPickValue)
        .where(
            FantasyCalcPickValue.is_dynasty == is_dynasty,
            FantasyCalcPickValue.num_qbs == num_qbs,
            FantasyCalcPickValue.num_teams == num_teams,
            FantasyCalcPickValue.ppr == ppr,
            FantasyCalcPickValue.season.in_(seasons),
            FantasyCalcPickValue.round.in_(rounds),
        )
        .order_by(
            FantasyCalcPickValue.season,
            FantasyCalcPickValue.round,
            FantasyCalcPickValue.is_exact_slot.desc(),
            FantasyCalcPickValue.slot,
        )
    )

    output: dict[tuple[str, int], list[FantasyCalcPickValue]] = defaultdict(list)

    for row in result.scalars().all():
        output[(row.season, row.round)].append(row)

    return dict(output)
