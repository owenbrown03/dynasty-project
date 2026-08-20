import pytest
from test_database_integration import transactional_session as _transactional_session

@pytest.fixture
async def transactional_session():
    """Yield an AsyncSession wrapped in a rollback‑on‑exit transaction.

    This re‑uses the async context manager defined in `test_database_integration.py`
    so that any test that requests the `transactional_session` fixture gets a fresh
    database session that is automatically rolled back after the test finishes.
    """
    async with _transactional_session() as session:
        yield session
