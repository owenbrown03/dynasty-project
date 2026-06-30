import logging

from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.db.sleeper.api import (
    InternalState,
    Player,
    PlayerProjection,
)

from app.crud.sleeper.projection import (
    upsert_projection,
)

from app.crud.sleeper.player import (
    sync_players,
)


logger = logging.getLogger(__name__)


SYNC_INTERVAL = timedelta(days=1)


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


    state = (
        await db.execute(
            select(InternalState)
            .where(
                InternalState.key == key
            )
        )
    ).scalar_one_or_none()


    if should_skip_sync(
        state,
        force_update,
    ):
        logger.info(
            "Projection sync skipped"
        )
        return


    logger.info(
        f"Starting Sleeper {season} projection sync"
    )


    projections = await sleeper.read.get_projections(
        season
    )


    players = await load_player_ids(db)


    inserted = 0
    skipped = 0


    for projection in projections:

        if projection.player_id not in players:
            skipped += 1

            logger.warning(
                f"Missing player {projection.player_id}"
            )

            continue


        if projection.stats.gp <= 0:
            skipped += 1
            continue


        row = build_projection(
            projection,
            season,
        )


        await upsert_projection(
            row,
            db,
        )

        inserted += 1


    await update_sync_state(
        db,
        state,
        key,
    )


    logger.info(
        f"""
        Projection sync complete

        Updated: {inserted}
        Skipped: {skipped}
        """
    )



async def load_player_ids(
    db: AsyncSession,
):

    result = await db.execute(
        select(Player.player_id)
    )

    return set(
        result.scalars().all()
    )



def build_projection(
    projection,
    season: int,
):

    stats = projection.stats.model_dump()


    return PlayerProjection(
        player_id=projection.player_id,
        season=season,
        source="sleeper",

        **stats,
    )



def should_skip_sync(
    state,
    force_update,
):

    if force_update:
        return False

    if not state or not state.value:
        return False


    last_update = datetime.fromisoformat(
        state.value
    )


    return (
        last_update >
        datetime.now() - SYNC_INTERVAL
    )



async def update_sync_state(
    db,
    state,
    key,
):

    if not state:

        state = InternalState(
            key=key
        )

        db.add(state)


    state.value = datetime.now().isoformat()

    await db.commit()