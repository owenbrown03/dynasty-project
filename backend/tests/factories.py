'''Factory helpers that build real Pydantic schema objects for tests.

The project already defines its database‑layer schemas under
`backend/app/models/db/sleeper/api.py` (and related files).  Importing those
schemas gives us the exact model definitions that the production code expects,
including required fields and validation logic.

These factories return fully‑populated objects with sensible dummy data.
They are deliberately tiny – just enough for the transformers to succeed.
If the import path changes, adjust accordingly – the tests will fail loudly.
''' 

from datetime import datetime, timezone
from uuid import uuid4

# Import the actual Pydantic models
from app.models.db.sleeper import api as sleeper_schema

def _dummy_str() -> str:
    """Return a short random string for unique fields."""
    return f"dummy-{uuid4().hex[:8]}"

def user_factory(**overrides) -> sleeper_schema.User:
    """Create a full `User` schema object."""
    data = {
        "user_id": _dummy_str(),
        "username": f"user_{_dummy_str()}",
        "display_name": "Test User",
        "avatar": "https://example.com/avatar.png",
        "metadata": {},
        "settings": {},
        "created": datetime.now(timezone.utc),
        "updated": datetime.now(timezone.utc),
    }
    data.update(overrides)
    return sleeper_schema.User(**data)

def roster_factory(**overrides) -> sleeper_schema.Roster:
    """Create a full `Roster` schema object."""
    data = {
        "roster_id": _dummy_str(),
        "owner_id": _dummy_str(),
        "league_id": _dummy_str(),
        "players": [],
        "settings": {},
        "metadata": {},
        "created": datetime.now(timezone.utc),
        "updated": datetime.now(timezone.utc),
    }
    data.update(overrides)
    return sleeper_schema.Roster(**data)

def league_factory(**overrides) -> sleeper_schema.League:
    data = {
        "league_id": _dummy_str(),
        "name": "Test League",
        "season": 2025,
        "type": "standard",
        "settings": {},
        "metadata": {},
        "created": datetime.now(timezone.utc),
        "updated": datetime.now(timezone.utc),
    }
    data.update(overrides)
    return sleeper_schema.League(**data)

def draft_factory(**overrides) -> sleeper_schema.Draft:
    data = {
        "draft_id": _dummy_str(),
        "league_id": _dummy_str(),
        "draft_order": [],
        "metadata": {},
        "created": datetime.now(timezone.utc),
        "updated": datetime.now(timezone.utc),
    }
    data.update(overrides)
    return sleeper_schema.Draft(**data)

def transaction_factory(**overrides) -> sleeper_schema.Transaction:
    data = {
        "transaction_id": _dummy_str(),
        "type": "trade",
        "status": "complete",
        "status_updated": datetime.now(timezone.utc),
        "adds": [],
        "drops": [],
        "waiver_budget": [],
        "draft_picks": [],
        "metadata": {},
    }
    data.update(overrides)
    return sleeper_schema.Transaction(**data)
