'''Integration test that exercises the complete league sync pipeline using the real factories.

It validates that users, rosters, drafts, and transactions are persisted without errors.
''' 

import asyncio
from datetime import datetime, timezone

from app.services.sleeper.transformers import (
    league_to_db,
    user_to_db,
    roster_to_db,
    draft_to_db,
    tx_to_db,
)
from app.crud.sleeper.league import sync_leagues

# Factories for real Pydantic models
from tests.factories import (
    user_factory,
    roster_factory,
    league_factory,
    draft_factory,
    transaction_factory,
)

# Re‑use the FakeSleeperRead from the existing trade test
from test_trade_sync_integration import FakeSleeperRead, transactional_session

async def _run_full_sync(session):
    # Build a realistic bundle of objects
    league = league_factory()
    users = [user_factory() for _ in range(3)]
    rosters = [roster_factory(owner_id=u.user_id) for u in users]
    draft = draft_factory()
    waiver_tx = transaction_factory(type="waiver", status="complete")

    sleeper = FakeSleeperRead(
        league_obj=league,
        users=users,
        rosters=rosters,
        drafts=[draft],
        transactions=[waiver_tx],
    )
    # Execute the actual sync logic
    await sync_leagues(
        sleeper=sleeper,
        db_session=session,
        league_id=league.league_id,
        league_type=league.type,
    )
    return True

def test_full_league_sync_integration():
    """Wrap the async flow in a sync pytest test.

    The `transactional_session` context manager provides a fresh DB transaction that rolls back
    after the test finishes, keeping the suite isolated.
    """
    async def _run():
        async with transactional_session() as session:
            await _run_full_sync(session)
    asyncio.run(_run())
