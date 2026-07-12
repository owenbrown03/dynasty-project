from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.db.sleeper.api import PlayerSeasonStats


async def upsert_player_season_stats(
    stats: PlayerSeasonStats,
    db: AsyncSession,
):
    stmt = select(PlayerSeasonStats).where(
        PlayerSeasonStats.player_id == stats.player_id,
        PlayerSeasonStats.season == stats.season,
        PlayerSeasonStats.season_type == stats.season_type,
        PlayerSeasonStats.source == stats.source,
    )

    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        for field in PlayerSeasonStats.model_fields:
            if field == "id":
                continue

            setattr(
                existing,
                field,
                getattr(stats, field),
            )
    else:
        db.add(stats)

    await db.commit()
    return existing or stats
