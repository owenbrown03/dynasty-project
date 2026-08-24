import asyncio
import json

from app.services.draft.rookie_war import (
    _load_shared_data,
    _sel_attr,
)


def _assert_all_fields(selection, expected_player_id="12345"):
    assert _sel_attr(selection, "player_id") == expected_player_id
    assert _sel_attr(selection, "season") == "2025"
    assert _sel_attr(selection, "round") == 2
    assert _sel_attr(selection, "round_slot") == 7


def test_sel_attr_handles_db_tuples():
    _assert_all_fields(("12345", "2025", 2, 7))


def test_sel_attr_handles_json_deserialized_lists():
    _assert_all_fields(["12345", "2025", 2, 7])


def test_sel_attr_handles_dicts():
    _assert_all_fields(
        {
            "player_id": "12345",
            "season": "2025",
            "round": 2,
            "round_slot": 7,
        }
    )


def test_sel_attr_returns_none_for_unknown_field():
    selection = ["12345", "2025", 2, 7]
    assert _sel_attr(selection, "unknown") is None


def test_load_shared_data_normalizes_cached_selections(monkeypatch):
    cached_payload = {
        "selections": [["12345", "2025", 2, 7], ["67890", "2024", 1, 3]],
        "stat_seasons": [2024, 2025],
    }

    class FakeRedis:
        async def get(self, key):
            return json.dumps(cached_payload)

    def _fail(*_args, **_kwargs):
        raise AssertionError("DB must not be hit when redis cache hits")

    monkeypatch.setattr(
        "app.services.draft.rookie_war.get_historical_rookie_draft_selections",
        _fail,
    )
    monkeypatch.setattr(
        "app.services.draft.rookie_war.get_available_stat_seasons",
        _fail,
    )

    shared = asyncio.run(
        _load_shared_data(
            db=None,
            redis=FakeRedis(),
            rounds=[1, 2],
        )
    )

    assert shared.stat_seasons == [2024, 2025]
    for selection in shared.selections:
        assert isinstance(selection, tuple)
        assert _sel_attr(selection, "player_id") is not None
