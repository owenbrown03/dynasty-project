import asyncio
from datetime import datetime, UTC
import pytest
from contextlib import asynccontextmanager
from sqlalchemy import text
from sqlmodel import select

from app.core.database import AsyncSessionLocal, engine
from app.models.db.auth import SiteUser
from app.models.db.sleeper.api import League, LeagueSyncState, Movement, Transaction
from types import SimpleNamespace
from app.crud.sleeper import league as league_crud


from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings


@asynccontextmanager
async def transactional_session():
    """
    Context manager that opens a database connection, begins a transaction,
    and yields an AsyncSession. When the context manager exits, the transaction
    is completely rolled back, leaving the database unmodified.
    """
    engine = create_async_engine(settings.async_database_url, echo=False)
    connection = await engine.connect()
    transaction = await connection.begin()
    
    session = AsyncSessionLocal(bind=connection)
    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()
        await engine.dispose()


def test_real_database_connection():
    """
    Verify that the test suite can connect to the real Postgres container,
    execute queries, and retrieve results.
    """
    async def _test():
        async with transactional_session() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
    
    asyncio.run(_test())


def test_real_database_transactional_rollback():
    """
    Verify that inserts into the database are rolled back automatically
    and do not persist or dirty the development database.
    """
    test_email = "temp_integration_test_user@example.com"
    
    async def _test():
        # Step 1: Insert user inside transaction 1
        async with transactional_session() as session1:
            user = SiteUser(
                email=test_email,
                hashed_password="fake_password_hash",
            )
            session1.add(user)
            await session1.commit()
            
            # Query inside transaction 1 to confirm it exists
            result = await session1.execute(
                select(SiteUser).where(SiteUser.email == test_email)
            )
            db_user = result.scalars().first()
            assert db_user is not None
            assert db_user.email == test_email

        # Step 2: Query inside transaction 2 to confirm user was rolled back
        async with transactional_session() as session2:
            result = await session2.execute(
                select(SiteUser).where(SiteUser.email == test_email)
            )
            db_user = result.scalars().first()
            assert db_user is None

    asyncio.run(_test())


def test_database_sync_state_timestamp_compatibility():
    """
    Verify that storing a timezone-naive UTC datetime in LeagueSyncState
    works seamlessly without any asyncpg driver-level offset mismatch errors.
    """
    async def _test():
        async with transactional_session() as session:
            # 1. Fetch an existing league to associate the sync state with
            result = await session.execute(select(League).limit(1))
            league = result.scalars().first()
            
            if not league:
                # No league exists in development database, skip the sync state insert test
                return
            
            # 2. Delete any existing sync state for this league inside transaction
            await session.execute(
                text("DELETE FROM leaguesyncstate WHERE league_id = :lid").bindparams(lid=league.league_id)
            )
            
            # 3. Create a new sync state with a timezone-naive UTC datetime
            naive_utc_now = datetime.now(UTC).replace(tzinfo=None)
            sync_state = LeagueSyncState(
                league_id=league.league_id,
                last_synced_week=1,
                last_synced_at=naive_utc_now,
            )
            
            session.add(sync_state)
            await session.commit()
            
            # 4. Fetch the inserted sync state and assert values
            result = await session.execute(
                select(LeagueSyncState).where(LeagueSyncState.league_id == league.league_id)
            )
            db_state = result.scalars().first()
            assert db_state is not None
            assert db_state.last_synced_week == 1
            # Retrieve time should match naive UTC now (within database resolution)
            assert abs((db_state.last_synced_at - naive_utc_now).total_seconds()) < 1.0

    asyncio.run(_test())


def test_save_transactions_real_db():
    """
    Verify that _save_transactions successfully stores transaction metadata and
    movement children in the real Postgres database.
    """
    async def _test():
        async with transactional_session() as session:
            # 1. Create and insert a test league
            league_id = "test-league-abc-123"
            league = League(
                league_id=league_id,
                name="Test League",
                season="2026",
                status="in_season",
                roster_positions=["QB", "RB", "WR", "TE"],
                scoring_settings={},
                settings={},
                total_rosters=12,
                draft_id="draft-test-123",
            )
            session.add(league)
            await session.commit()

            # 2. Build mock Transaction namespace
            transaction = SimpleNamespace(
                transaction_id="txn-drop-real-1",
                type="waiver",
                status="complete",
                status_updated=123456789,
                adds={},
                drops={"player-1": 9},
                waiver_budget=[],
                draft_picks=[],
            )

            # 3. Call the actual crud function to save it to Postgres
            await league_crud._save_transactions(
                db=session,
                transactions=[transaction],
                league_id=league_id,
            )
            await session.commit()

            # 4. Query the real tables to verify insertion
            tx_result = await session.execute(
                select(Transaction).where(Transaction.transaction_id == "txn-drop-real-1")
            )
            db_tx = tx_result.scalars().first()
            assert db_tx is not None
            assert db_tx.league_id == league_id
            assert db_tx.type == "waiver"

            mv_result = await session.execute(
                select(Movement).where(Movement.transaction_id == "txn-drop-real-1")
            )
            db_mvs = mv_result.scalars().all()
            assert len(db_mvs) == 1
            assert db_mvs[0].player_id == "player-1"
            assert db_mvs[0].roster_id == 9
            assert db_mvs[0].action == "DROP"

    asyncio.run(_test())
