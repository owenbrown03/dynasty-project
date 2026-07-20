import logging
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import AsyncSessionLocal
from app.crud.fc.sync import sync_fantasycalc_values
from app.crud.ktc.sync import sync_ktc_values
from app.crud.sleeper.player import sync_players
from app.crud.underdog.sync import sync_underdog_adp
from app.infrastructure.http.manager import HTTPClientManager
from app.infrastructure.redis.manager import RedisManager
from app.integrations.fc.client import FantasyCalcClient
from app.integrations.ktc.client import KTCClient
from app.integrations.sleeper.singleton import get_worker_sleeper_client
from app.integrations.underdog.client import UnderdogClient
from app.models.db.sleeper.api import InternalState
from app.services.adp.maintenance import run_adp_maintenance
from app.services.sleeper.projection import sync_projections
from app.services.sleeper.season_stats import sync_recent_regular_season_stats

logger = logging.getLogger(__name__)

DAILY_EXTERNAL_SYNC_STATE_KEY = "sync:external:daily:last_run_at"
DAILY_EXTERNAL_SYNC_INTERVAL = timedelta(days=1)
DAILY_EXTERNAL_SYNC_LOCK_KEY = "sync:external:daily:lock"
DAILY_EXTERNAL_SYNC_LOCK_TTL_SECONDS = 6 * 60 * 60


def parse_sync_timestamp(
    value: str | None,
) -> datetime | None:
    if not value:
        return None

    return datetime.fromisoformat(
        value,
    )


def should_run_daily_external_sync(
    last_run_at: datetime | None,
    *,
    now: datetime | None = None,
    force: bool = False,
) -> bool:
    if force:
        return True

    if last_run_at is None:
        return True

    current = now or datetime.now()
    return (
        last_run_at
        <= current - DAILY_EXTERNAL_SYNC_INTERVAL
    )


async def get_daily_external_sync_state(
    db: AsyncSession,
) -> InternalState | None:
    result = await db.execute(
        select(InternalState).where(
            InternalState.key == DAILY_EXTERNAL_SYNC_STATE_KEY,
        )
    )

    return result.scalar_one_or_none()


async def update_daily_external_sync_state(
    db: AsyncSession,
    state: InternalState | None,
    *,
    ran_at: datetime | None = None,
) -> None:
    if state is None:
        state = InternalState(
            key=DAILY_EXTERNAL_SYNC_STATE_KEY,
            value="",
        )
        db.add(state)

    state.value = (
        ran_at or datetime.now()
    ).isoformat()
    db.add(state)
    await db.commit()


async def acquire_daily_external_sync_lock() -> str | None:
    redis = await RedisManager.get()
    token = datetime.now().isoformat()

    acquired = await redis.set(
        DAILY_EXTERNAL_SYNC_LOCK_KEY,
        token,
        ex=DAILY_EXTERNAL_SYNC_LOCK_TTL_SECONDS,
        nx=True,
    )

    if acquired:
        return token

    return None


async def release_daily_external_sync_lock(
    token: str,
) -> None:
    redis = await RedisManager.get()
    current = await redis.get(
        DAILY_EXTERNAL_SYNC_LOCK_KEY,
    )

    if current == token:
        await redis.delete(
            DAILY_EXTERNAL_SYNC_LOCK_KEY,
        )


async def run_daily_external_syncs(
    *,
    force: bool = False,
) -> dict:
    lock_token = await acquire_daily_external_sync_lock()

    if lock_token is None:
        logger.info(
            "Skipping daily external sync because one is already running",
        )
        return {
            "status": "skipped",
            "reason": "already_running",
        }

    try:
        async with AsyncSessionLocal() as db:
            state = await get_daily_external_sync_state(
                db,
            )
            last_run_at = parse_sync_timestamp(
                state.value if state else None,
            )

            if not should_run_daily_external_sync(
                last_run_at,
                force=force,
            ):
                logger.info(
                    "Skipping daily external sync because it ran recently at %s",
                    last_run_at.isoformat() if last_run_at else "unknown",
                )
                return {
                    "status": "skipped",
                    "reason": "fresh",
                    "last_run_at": (
                        last_run_at.isoformat()
                        if last_run_at else None
                    ),
                }

            sleeper = await get_worker_sleeper_client()
            http_client = await HTTPClientManager.get()
            ktc = KTCClient(http=http_client)
            fc = FantasyCalcClient(http=http_client)
            underdog = UnderdogClient(http=http_client)
            season = datetime.now().year

            logger.info(
                "Starting daily external sync bundle for season %s",
                season,
            )

            await sync_players(
                db=db,
                sleeper=sleeper,
                force_update=True,
            )
            await sync_projections(
                db=db,
                sleeper=sleeper,
                season=season,
                force_update=True,
            )
            await sync_recent_regular_season_stats(
                db=db,
                sleeper=sleeper,
                current_season=season,
                force_update=True,
            )

            ktc_result = await sync_ktc_values(
                db=db,
                ktc=ktc,
            )
            fantasycalc_result = await sync_fantasycalc_values(
                db=db,
                fc=fc,
            )
            underdog_result = await sync_underdog_adp(
                db=db,
                underdog=underdog,
            )
            adp_result = await run_adp_maintenance(
                db,
                sleeper,
                seed_source="users",
                seed_limit=250,
                cycles=3,
                max_nodes_per_cycle=50,
                max_drafts_per_cycle=200,
                allow_when_disabled=True,
                discover_users=False,
            )

            ran_at = datetime.now()
            await update_daily_external_sync_state(
                db,
                state,
                ran_at=ran_at,
            )

            logger.info(
                "Completed daily external sync bundle at %s",
                ran_at.isoformat(),
            )

            return {
                "status": "complete",
                "ran_at": ran_at.isoformat(),
                "season": season,
                "ktc": ktc_result,
                "fantasycalc": fantasycalc_result,
                "underdog": underdog_result,
                "adp": {
                    "seeded_count": adp_result.seeded_count,
                    "completed_cycles": adp_result.completed_cycles,
                    "total_processed_nodes": adp_result.total_processed_nodes,
                    "total_discovered_drafts": adp_result.total_discovered_drafts,
                    "total_ingested_drafts": adp_result.total_ingested_drafts,
                    "total_qualified_drafts": adp_result.total_qualified_drafts,
                    "stopped_reason": adp_result.stopped_reason,
                },
            }
    finally:
        await release_daily_external_sync_lock(
            lock_token,
        )
