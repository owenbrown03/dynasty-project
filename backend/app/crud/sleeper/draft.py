from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.db.sleeper.api import Draft, TradedPick, Transaction


async def get_drafts_by_league_ids(
    db: AsyncSession,
    league_ids: list[str],
) -> dict[str, list[Draft]]:
    if not league_ids:
        return {}

    result = await db.execute(
        select(Draft)
        .where(
            Draft.league_id.in_(league_ids),
        )
        .order_by(
            Draft.league_id,
            Draft.season.desc(),
        )
    )

    drafts_by_league_id: dict[str, list[Draft]] = defaultdict(list)

    for draft in result.scalars():
        drafts_by_league_id[draft.league_id].append(draft)

    return dict(drafts_by_league_id)


async def get_traded_picks_by_league_ids(
    db: AsyncSession,
    league_ids: list[str],
) -> dict[str, list[tuple[TradedPick, int]]]:
    if not league_ids:
        return {}

    result = await db.execute(
        select(
            TradedPick,
            Transaction.time_ms,
        )
        .outerjoin(
            Transaction,
            Transaction.transaction_id == TradedPick.transaction_id,
        )
        .where(
            TradedPick.league_id.in_(league_ids),
        )
        .order_by(
            TradedPick.league_id,
            Transaction.time_ms.asc().nullsfirst(),
            TradedPick.id.asc(),
        )
    )

    traded_picks_by_league_id: dict[
        str,
        list[tuple[TradedPick, int]],
    ] = defaultdict(list)

    for traded_pick, time_ms in result.all():
        traded_picks_by_league_id[traded_pick.league_id].append(
            (
                traded_pick,
                time_ms or 0,
            )
        )

    return dict(traded_picks_by_league_id)
