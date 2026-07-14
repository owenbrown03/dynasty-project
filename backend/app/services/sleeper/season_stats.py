import logging
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.sleeper.player import sync_players
from app.crud.sleeper.season_stats import upsert_player_season_stats
from app.models.db.sleeper.api import InternalState, Player, PlayerSeasonStats


logger = logging.getLogger(__name__)

SYNC_INTERVAL = timedelta(days=7)
SYNCABLE_STAT_FIELDS = {
    "pass_att",
    "pass_cmp",
    "pass_yd",
    "pass_td",
    "pass_int",
    "pass_2pt",
    "rush_att",
    "rush_yd",
    "rush_td",
    "rush_2pt",
    "rec",
    "rec_yd",
    "rec_td",
    "rec_2pt",
    "fum_lost",
    "pass_fd",
    "rush_fd",
    "rec_fd",
    "rec_0_4",
    "rec_5_9",
    "rec_10_19",
    "rec_20_29",
    "rec_30_39",
    "rec_40p",
    "bonus_rec_rb",
    "bonus_rec_wr",
    "bonus_rec_te",
}


async def sync_recent_regular_season_stats(
    *,
    db: AsyncSession,
    sleeper,
    current_season: int,
    years: int = 16,
    force_update: bool = False,
) -> None:
    start_season = max(
        current_season - years,
        2017,
    )

    for season in range(start_season, current_season):
        await sync_regular_season_stats(
            db=db,
            sleeper=sleeper,
            season=season,
            force_update=force_update,
        )


async def sync_regular_season_stats(
    *,
    db: AsyncSession,
    sleeper,
    season: int,
    force_update: bool = False,
) -> None:
    await sync_players(
        db=db,
        sleeper=sleeper,
        force_update=False,
    )

    key = f"sync:season-stats:sleeper:regular:{season}"
    state = (
        await db.execute(
            select(InternalState).where(
                InternalState.key == key,
            )
        )
    ).scalar_one_or_none()

    if should_skip_sync(
        state,
        force_update,
    ):
        logger.info(
            "Season stats sync skipped for %s",
            season,
        )
        return

    logger.info(
        "Starting Sleeper %s regular season stats sync",
        season,
    )

    raw_stats = await sleeper.read.get_regular_season_stats(
        season,
    )
    player_ids = await load_player_ids(
        db,
    )

    inserted = 0
    skipped = 0

    for player_id, stats in raw_stats.items():
        if str(player_id).startswith("TEAM_"):
            skipped += 1
            continue

        if player_id not in player_ids:
            skipped += 1
            continue

        row = build_player_season_stats(
            player_id=player_id,
            season=season,
            stats=stats,
        )

        if row.games_played <= 0:
            skipped += 1
            continue

        await upsert_player_season_stats(
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
        "Season stats sync complete for %s. Updated=%s Skipped=%s",
        season,
        inserted,
        skipped,
    )


async def load_player_ids(
    db: AsyncSession,
) -> set[str]:
    result = await db.execute(
        select(Player.player_id)
    )
    return set(
        result.scalars().all()
    )


def build_player_season_stats(
    *,
    player_id: str,
    season: int,
    stats: dict,
) -> PlayerSeasonStats:
    values = {
        key: float(stats.get(key, 0) or 0)
        for key in SYNCABLE_STAT_FIELDS
    }

    return PlayerSeasonStats(
        player_id=player_id,
        season=season,
        season_type="regular",
        source="sleeper",
        games_played=float(stats.get("gp", 0) or 0),
        **values,
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
            key=key,
        )
        db.add(state)

    state.value = datetime.now().isoformat()
    await db.commit()
