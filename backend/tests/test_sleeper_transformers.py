from types import SimpleNamespace

from app.crud.base import _normalize_bulk_mappings
from app.models.db.sleeper.api import User
from app.services.sleeper import transformers


def test_normalize_bulk_mappings_rectangularizes_rows():
    normalized = _normalize_bulk_mappings(
        User,
        [
            {
                "user_id": "1",
                "display_name": "One",
                "is_owner": True,
            },
            {
                "user_id": "2",
                "display_name": "Two",
            },
        ],
    )

    assert normalized == [
        {
            "display_name": "One",
            "user_id": "1",
        },
        {
            "display_name": "Two",
            "user_id": "2",
        },
    ]


def test_tx_to_db_uses_status_updated_timestamp():
    transaction, movements, waivers, picks = transformers.tx_to_db(
        SimpleNamespace(
            transaction_id="txn-1",
            type="trade",
            status="complete",
            status_updated=123,
            adds=None,
            drops=None,
            waiver_budget=[],
            draft_picks=[],
        ),
        league_id="league-1",
    )

    assert transaction.time_ms == 123
    assert movements == []
    assert waivers == []
    assert picks == []


def test_tx_to_db_falls_back_to_legacy_time_field():
    transaction, *_ = transformers.tx_to_db(
        SimpleNamespace(
            transaction_id="txn-2",
            type="trade",
            status=None,
            time=456,
            adds=None,
            drops=None,
            waiver_budget=[],
            draft_picks=[],
        ),
        league_id="league-1",
    )

    assert transaction.time_ms == 456
