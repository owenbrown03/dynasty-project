import asyncio

import pytest

from app.services.advisor.trade_block import (
    TradeBlockSnapshot,
    _snapshot_from_json,
    _snapshot_to_json,
)


def _entry(player_id, settings):
    return {
        "league_id": "L1",
        "player_id": player_id,
        "settings": settings,
    }


def test_snapshot_parses_blocked_players_and_picks():
    snapshot = TradeBlockSnapshot.from_league_players(
        [
            _entry("4046", {"otb": 3, "otb_added_at": 1}),
            _entry("1423", None),
            _entry("10,2026,2", {"otb": 10}),
            _entry("12,2025,4", {"otb": 8}),
            _entry("", {"otb": 2}),
            _entry("garbage,id", {"otb": 2}),
        ]
    )

    assert snapshot.player_ids == {"4046": 3}
    assert snapshot.picks == {
        (10, "2026", 2): 10,
        (12, "2025", 4): 8,
    }


def test_snapshot_roundtrip_preserves_entries():
    snapshot = TradeBlockSnapshot.from_league_players(
        [
            _entry("4046", {"otb": 3}),
            _entry("5,2025,1", {"otb": 7}),
        ]
    )

    restored = _snapshot_from_json(_snapshot_to_json(snapshot))

    assert restored.player_ids == snapshot.player_ids
    assert restored.picks == snapshot.picks


def test_get_trade_block_snapshot_uses_cache():
    from app.services.advisor import trade_block as tb

    calls = {"count": 0}

    class FakeRead:
        async def get_league_players_status(self, league_id):
            calls["count"] += 1
            return [_entry("4046", {"otb": 3})]

    class FakeClient:
        read = FakeRead()

    class FakeRedis:
        def __init__(self):
            self.store = {}

        async def get(self, key):
            return self.store.get(key)

        async def set(self, key, value, ttl_seconds=None):
            self.store[key] = value

    class Ctx:
        sleeper = FakeClient()
        redis = FakeRedis()

    ctx = Ctx()

    first = asyncio.run(
        tb.get_trade_block_snapshot(ctx, "league-1")
    )
    second = asyncio.run(
        tb.get_trade_block_snapshot(ctx, "league-1")
    )

    assert calls["count"] == 1
    assert first.player_ids == second.player_ids
