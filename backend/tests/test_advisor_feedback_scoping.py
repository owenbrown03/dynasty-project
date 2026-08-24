import asyncio
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.crud.sleeper.advisor import (
    FEEDBACK_ACTIVE_TTL_DAYS,
    get_active_feedback_by_site_user,
    resolve_feedback,
)
from app.models.db.auth import SiteUser
from app.models.db.sleeper.api import League
from app.models.db.sleeper.personal import AdvisorFeedback


@asynccontextmanager
async def transactional_session():
    connection_engine = create_async_engine(
        settings.async_database_url,
        echo=False,
    )
    connection = await connection_engine.connect()
    transaction = await connection.begin()

    session = AsyncSessionLocal(bind=connection)
    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()
        await connection_engine.dispose()


def _league(league_id: str) -> League:
    return League(
        league_id=league_id,
        name=f"Test {league_id}",
        season="2026",
        type="redraft",
        total_rosters=12,
        draft_id=f"draft-{league_id}",
    )


def _feedback(
    site_user_id,
    league_id,
    *,
    age_days: int = 0,
) -> AdvisorFeedback:
    created = datetime.utcnow() - timedelta(days=age_days)
    return AdvisorFeedback(
        site_user_id=site_user_id,
        league_id=league_id,
        counterparty_id=None,
        player_ids=[],
        sentiment="dislike",
        reason="test dislike",
        tags=[],
        proposal_snapshot={},
        action_taken=None,
        resolved=False,
        created_at=created,
    )


def test_feedback_scope_and_expiry():
    async def _run():
        async with transactional_session() as db:
            user = SiteUser(
                email=f"advisor-feedback-{uuid.uuid4()}@test.local",
                hashed_password="x",
            )
            db.add(user)
            await db.flush()

            league_a = _league(f"fb-a-{uuid.uuid4().hex[:8]}")
            league_b = _league(f"fb-b-{uuid.uuid4().hex[:8]}")
            db.add_all([league_a, league_b])
            await db.flush()

            db.add_all(
                [
                    _feedback(user.id, league_a.league_id),
                    _feedback(user.id, league_b.league_id),
                    _feedback(user.id, league_a.league_id),
                    _feedback(
                        user.id,
                        league_a.league_id,
                        age_days=FEEDBACK_ACTIVE_TTL_DAYS + 30,
                    ),
                ]
            )
            await db.commit()

            scoped = await get_active_feedback_by_site_user(
                db,
                site_user_id=user.id,
                league_ids=[league_a.league_id],
            )
            assert len(scoped) == 2
            assert all(
                row.league_id == league_a.league_id
                for row in scoped
            )

            unscoped = await get_active_feedback_by_site_user(
                db,
                site_user_id=user.id,
            )
            assert len(unscoped) == 3

            no_ttl = await get_active_feedback_by_site_user(
                db,
                site_user_id=user.id,
                active_within_days=None,
            )
            assert len(no_ttl) == 4

            target = scoped[0]
            assert (
                await resolve_feedback(
                    db,
                    site_user_id=user.id,
                    feedback_id=target.id,
                )
                is True
            )

            after_resolve = await get_active_feedback_by_site_user(
                db,
                site_user_id=user.id,
                league_ids=[league_a.league_id],
            )
            assert len(after_resolve) == 1

    asyncio.run(_run())


def test_resolve_missing_feedback_returns_false():
    async def _run():
        async with transactional_session() as db:
            assert (
                await resolve_feedback(
                    db,
                    site_user_id=uuid.uuid4(),
                    feedback_id=999999999,
                )
                is False
            )

    asyncio.run(_run())
