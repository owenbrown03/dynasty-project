import logging

from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.db.sleeper.api import InternalState, Player, PlayerProjection
from app.crud.sleeper.projection import upsert_projection
from app.crud.sleeper.player import sync_players

logger = logging.getLogger(__name__)


async def sync_projections(
    db: AsyncSession,
    sleeper,
    season: int,
    force_update: bool = False,
):

    await sync_players(
        db=db,
        sleeper=sleeper,
        force_update=False,
    )


    key = f"sync:projection:sleeper:{season}"


    result = await db.execute(
        select(InternalState)
        .where(
            InternalState.key == key
        )
    )

    state = result.scalar_one_or_none()


    last_update = (
        datetime.fromisoformat(state.value)
        if state and state.value
        else None
    )


    if (
        not force_update
        and last_update
        and last_update >
        datetime.now() - timedelta(days=1)
    ):
        logger.info(
            "Projection sync skipped"
        )
        return


    logger.info(
        f"Starting Sleeper {season} projection sync..."
    )


    projections = await sleeper.read.get_projections(
        season
    )

    count = 0
    skipped = 0


    for projection in projections:

        if projection.stats.pts_ppr is None:
            continue

        if projection.stats.pts_ppr <= 0:
            skipped += 1
            continue

        player_exists = await db.get(
            Player,
            projection.player_id,
        )

        if not player_exists:
            skipped += 1

            logger.warning(
                f"Missing player {projection.player_id}, skipping projection"
            )

            continue


        row = PlayerProjection(
            player_id=projection.player_id,
            season=season,
            source="sleeper",
            scoring_format="ppr",
            projected_points=projection.stats.pts_ppr,
            projected_ppg=projection.stats.pts_ppr / projection.stats.gp,
        )


        await upsert_projection(
            row,
            db,
        )

        count += 1


    if not state:
        state = InternalState(
            key=key
        )

        db.add(state)


    state.value = (
        datetime.now()
        .isoformat()
    )


    await db.commit()


    logger.info(
        f"Projection sync complete. "
        f"Inserted/updated: {count}, "
        f"Skipped: {skipped}"
    )