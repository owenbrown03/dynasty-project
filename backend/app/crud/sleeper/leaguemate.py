import logging, asyncio
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.sleeper.client import SleeperClient
from app.models.db.sleeper import api as model
from app.crud.sleeper.league import sync_leagues
from app.crud.sleeper.user import get_userid_by_username
from app.core.concurrency import bounded_gather

logger = logging.getLogger(__name__)


async def get_leaguemate_ids(
    db: AsyncSession,
    main_user_id: str,
):

    my_leagues = (
        select(model.Roster.league_id)
        .where(model.Roster.owner_id == main_user_id)
        .scalar_subquery()
    )

    stmt = (
        select(model.Roster.owner_id)
        .where(
            model.Roster.league_id.in_(my_leagues),
            model.Roster.owner_id != main_user_id,
            model.Roster.owner_id.is_not(None),
        )
        .distinct()
    )

    result = await db.execute(stmt)
    return result.scalars().all()


async def sync_leaguemates(
    db: AsyncSession,
    sleeper: SleeperClient,
    username: str,
):
    state = await sleeper.read.get_nfl_state()
    season = state.season
    curr_week = state.week

    main_user_id = await get_userid_by_username(db, sleeper, username)
    lm_ids = await get_leaguemate_ids(db, main_user_id)

    total = len(lm_ids)
    if total == 0:
        return {"status": "skipped", "synced_count": 0}

    logger.info(f"Processing {total} leaguemates")

    processed = 0
    log_step = max(1, total // 10)
    lock = asyncio.Lock()

    async def fetch(lm_id):
        nonlocal processed

        try:
            return await sleeper.read.get_leagues(lm_id, season)
        finally:
            async with lock:
                processed += 1
                if processed % log_step == 0 or processed == total:
                    logger.info(f"[Leaguemates] {processed}/{total}")

    api_results = await bounded_gather((fetch(lm_id) for lm_id in lm_ids))

    leagues = []
    for r in api_results:
        if isinstance(r, list):
            leagues.extend(r)
        elif isinstance(r, Exception):
            logger.error(f"leaguemate fetch failed: {r}")

    if not leagues:
        return {"status": "skipped", "reason": "no_leagues"}

    return await sync_leagues(db, leagues, curr_week, sleeper)