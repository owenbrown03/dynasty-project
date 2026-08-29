import asyncio
import logging
from fastapi import HTTPException, status
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.sleeper.api import User
from app.integrations.sleeper.client import SleeperClient
from app.crud.sleeper.league import sync_leagues

logger = logging.getLogger(__name__)
SLEEPER_HISTORY_START_SEASON = 2017
HISTORICAL_SYNC_WEEK = 18

async def get_userid_by_username(db: AsyncSession, sleeper: SleeperClient, username: str) -> str:
    clean_username = username.strip()

    try:
        username_details = await sleeper.read.get_user_details_by_username(clean_username)
        if username_details and username_details.user_id:
            db_user = await db.get(User, username_details.user_id)
            if not db_user:
                db_user = User(
                    user_id=username_details.user_id,
                    display_name=username_details.display_name,
                    avatar=username_details.avatar,
                )
                db.add(db_user)
            else:
                db_user.display_name = username_details.display_name
                db_user.avatar = username_details.avatar
                db.add(db_user)
            await db.commit()
            return username_details.user_id
    except Exception as exc:
        logger.warning(
            "Failed to fetch live Sleeper user details for %s: %s",
            clean_username,
            exc,
        )

    result = await db.execute(select(User.user_id).where(User.display_name == clean_username))
    user_id = result.scalar_one_or_none()
    if user_id:
        return user_id

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"User '{clean_username}' could not be resolved."
    )


async def get_username_by_userid(db: AsyncSession, sleeper: SleeperClient, user_id: str) -> str:
    """
    Looks up the user ID locally first to completely bypass the network semaphore.
    Falls back to the network ONLY if it's a completely new user profile signature.
    """
    result = await db.execute(select(User.display_name).where(User.user_id == user_id))
    username = result.scalar_one_or_none()
    if not username:
        user_id_details = await sleeper.read.get_user_details_by_username(user_id)
        if not user_id_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{user_id}' could not be resolved."
            )
        return user_id_details.display_name
    return username

async def get_user_meta_map(db: AsyncSession) -> dict[str, dict]:
    """Returns a dict of {user_id: {"name": display_name, "avatar": avatar}}"""
    result = await db.execute(
        select(User.user_id, User.display_name, User.avatar)
    )
    rows = result.all()

    return {
        user_id: {"name": display_name, "avatar": avatar}
        for user_id, display_name, avatar in rows
    }

async def sync_user_data(db: AsyncSession, sleeper: SleeperClient, username: str) -> dict:
    user_id = await get_userid_by_username(db, sleeper, username)
    state = await sleeper.read.get_nfl_state()
    current_season = int(state.season)
    curr_week = state.effective_week if hasattr(state, "effective_week") else max(int(state.week), 1)

    seasons = list(range(
        current_season,
        SLEEPER_HISTORY_START_SEASON - 1,
        -1,
    ))

    season_leagues = await asyncio.gather(
        *[
            sleeper.read.get_leagues(user_id, str(season))
            for season in seasons
        ],
        return_exceptions=True,
    )

    season_summaries: list[dict] = []
    total_synced_count = 0
    total_failed_batches = 0

    for season, leagues_result in zip(seasons, season_leagues):
        if isinstance(leagues_result, Exception):
            logger.warning(
                "Failed to fetch leagues for season %s: %s",
                season,
                leagues_result,
            )
            continue

        if not leagues_result:
            continue

        is_current_season = season == current_season
        season_result = await sync_leagues(
            db,
            leagues_result,
            curr_week if is_current_season else HISTORICAL_SYNC_WEEK,
            sleeper,
            force=is_current_season,
            existing_refresh=(
                "full"
                if is_current_season
                else "transactions_only"
            ),
            user_id=user_id if is_current_season else None,
            is_current_season=is_current_season,
        )

        season_summaries.append(
            {
                "season": str(season),
                **season_result,
            }
        )
        total_synced_count += season_result.get(
            "synced_count",
            0,
        )
        total_failed_batches += season_result.get(
            "failed_batches",
            0,
        )

    if not season_summaries:
        return {"status": "skipped", "reason": "no_leagues"}

    return {
        "status": "completed",
        "synced_count": total_synced_count,
        "failed_batches": total_failed_batches,
        "season_summaries": season_summaries,
    }

async def get_users(db: AsyncSession, user_ids: set[str]):
    if not user_ids:
        return {}

    result = await db.execute(
        select(User)
        .where(
            User.user_id.in_(user_ids)
        )
    )

    return {
        user.user_id: user
        for user in result.scalars()
    }

async def get_user_names_by_id(
    *,
    db: AsyncSession,
    user_ids: set[str],
) -> dict[str, str]:
    """
    Returns human-readable Sleeper display names for potential trade partners.
    """

    if not user_ids:
        return {}

    result = await db.execute(
        select(
            User.user_id,
            User.display_name,
        ).where(
            User.user_id.in_(
                user_ids,
            )
        )
    )

    return {
        user_id: (
            display_name
            or user_id
        )
        for user_id, display_name in result.all()
    }
