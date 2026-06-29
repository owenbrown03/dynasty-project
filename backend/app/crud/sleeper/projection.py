from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.db.sleeper.api import PlayerProjection


async def upsert_projection(
    projection: PlayerProjection,
    db: AsyncSession,
):

    stmt = select(PlayerProjection).where(
        PlayerProjection.player_id == projection.player_id,
        PlayerProjection.season == projection.season,
        PlayerProjection.source == projection.source,
        PlayerProjection.scoring_format == projection.scoring_format,
    )


    result = await db.execute(stmt)

    existing = result.scalar_one_or_none()


    if existing:

        existing.projected_points = (
            projection.projected_points
        )

        existing.projected_ppg = (
            projection.projected_ppg
        )

    else:
        db.add(projection)


    await db.commit()

    return existing or projection