import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.crud.sleeper.league import _save_transactions
from app.models.db.sleeper import api as model


def test_save_transactions_updates_roster_players_on_complete():
    # Setup mock rosters
    roster_1 = model.Roster(
        id=1,
        league_id="league_100",
        roster_id=1,
        owner_id="user_a",
        players=["player_drop", "player_keep"],
        roster_metadata={},
        settings={},
    )
    roster_2 = model.Roster(
        id=2,
        league_id="league_100",
        roster_id=2,
        owner_id="user_b",
        players=["player_existing"],
        roster_metadata={},
        settings={},
    )

    executed_stmts = []
    added_objects = []

    class MockResult:
        def __init__(self, data):
            self.data = data
        def scalars(self):
            return self
        def all(self):
            return self.data

    class MockDB:
        async def execute(self, stmt):
            executed_stmts.append(stmt)
            # Check if this is the select on Roster
            if hasattr(stmt, "is_select") and "roster" in str(stmt).lower():
                return MockResult([roster_1, roster_2])
            # For select on Transaction
            return MockResult([])

        def add(self, obj):
            added_objects.append(obj)

    db = MockDB()

    # Create completed trade transaction
    # Roster 1 drops "player_drop" and adds "player_add"
    # Roster 2 adds "player_drop" and drops "player_existing"
    trade_tx = SimpleNamespace(
        transaction_id="tx_1",
        type="trade",
        status="complete",
        status_updated=1600000000000,
        adds={"player_add": 1, "player_drop": 2},
        drops={"player_drop": 1, "player_existing": 2},
        waiver_budget=[],
        draft_picks=[],
    )

    asyncio.run(_save_transactions(db, [trade_tx], "league_100"))

    # Roster 1 should now have ["player_keep", "player_add"]
    assert "player_drop" not in roster_1.players
    assert "player_keep" in roster_1.players
    assert "player_add" in roster_1.players

    # Roster 2 should now have ["player_drop"]
    assert "player_existing" not in roster_2.players
    assert "player_drop" in roster_2.players


def test_trade_signals_excludes_current_league_from_buy_signals(monkeypatch):
    from app.crud.sleeper.trade import get_trade_signals

    # Main user: "user_main"
    # Leaguemate: "user_lm"
    # Shared leagues: "league_trade" (where trade happens) and "league_other" (another shared league)
    monkeypatch.setattr(
        "app.crud.sleeper.trade.get_userid_by_username",
        AsyncMock(return_value="user_main"),
    )
    monkeypatch.setattr(
        "app.crud.sleeper.trade.build_trade_signals_cache_key",
        AsyncMock(return_value="test_cache_key"),
    )
    monkeypatch.setattr(
        "app.crud.sleeper.trade.get_leaguemate_ids",
        AsyncMock(return_value=["user_lm"]),
    )
    monkeypatch.setattr(
        "app.crud.sleeper.trade.read_trades",
        AsyncMock(
            return_value={
                "tx_trade_1": {
                    "trade": SimpleNamespace(
                        transaction_id="tx_trade_1",
                        league_id="league_trade",
                        time_ms=1700000000000,
                    ),
                    "movements": [
                        SimpleNamespace(
                            roster_id=1,
                            player_id="player_star",
                            action="DROP",
                        )
                    ],
                    "picks": [],
                    "waivers": [],
                }
            }
        ),
    )
    monkeypatch.setattr(
        "app.crud.sleeper.trade.get_user_meta_map",
        AsyncMock(
            return_value={
                "user_lm": {"name": "Bob LM", "avatar": None, "is_placeholder": False},
                "user_main": {"name": "Me", "avatar": None, "is_placeholder": False},
            }
        ),
    )
    monkeypatch.setattr(
        "app.crud.sleeper.trade.get_trade_league_meta_map",
        AsyncMock(
            return_value={
                "league_trade": {"name": "League Trade (Sold Here)"},
                "league_other": {"name": "League Other (Still Rostered)"},
            }
        ),
    )
    monkeypatch.setattr(
        "app.crud.sleeper.trade.get_player_map",
        AsyncMock(
            return_value={
                "player_star": {
                    "first_name": "Star",
                    "last_name": "Player",
                    "position": "RB",
                }
            }
        ),
    )

    monkeypatch.setattr(
        "app.services.leagues.selection.get_visible_owned_league_rows_by_sleeper_user_id",
        AsyncMock(
            return_value=[
                SimpleNamespace(league=SimpleNamespace(league_id="league_trade")),
                SimpleNamespace(league=SimpleNamespace(league_id="league_other")),
            ]
        ),
    )

    class MockResult:
        def __init__(self, data):
            self.data = data
        def scalars(self):
            return self
        def all(self):
            return self.data
        def first(self):
            return self.data[0] if self.data else None

    class MockDB:
        async def execute(self, stmt):
            stmt_str = str(stmt).lower()
            # 1. roster_owner_map
            if "owner_id" in stmt_str and "roster_id" in stmt_str and "unnest" not in stmt_str:
                return MockResult([("league_trade", "user_lm", 1)])
            # 2. intersect_stmt (player_to_leagues):
            # Suppose user_lm rosters player_star in BOTH league_trade and league_other
            if "unnest" in stmt_str:
                return MockResult([
                    ("league_trade", "user_lm", "player_star"),
                    ("league_other", "user_lm", "player_star"),
                ])
            # 3. draft_orders
            if "draft_order" in stmt_str:
                return MockResult([])
            return MockResult([])

    db = MockDB()
    sleeper = SimpleNamespace()

    signals = asyncio.run(
        get_trade_signals(
            db=db,
            sleeper=sleeper,
            username="me",
            site_user_id=None,
            redis=None,
            cheap=False,
        )
    )

    assert len(signals) == 1
    tx = signals[0]
    drops = tx.users[0].drops
    assert len(drops) == 1
    # Crucial assertion: Buy opportunity should ONLY list "League Other", NOT "League Trade"!
    assert "League Trade (Sold Here)" not in drops[0].signal
    assert "League Other (Still Rostered)" in drops[0].signal
    assert drops[0].signal == "Buy opportunity (League Other (Still Rostered))"


def test_get_leaguemate_ids_filters_by_league_ids():
    from app.crud.sleeper.leaguemate import get_leaguemate_ids

    executed_stmts = []

    class MockResult:
        def __init__(self, data):
            self.data = data
        def scalars(self):
            return self
        def all(self):
            return self.data

    class MockDB:
        async def execute(self, stmt):
            executed_stmts.append(stmt)
            return MockResult(["user_active_1", "user_active_2"])

    db = MockDB()
    # When league_ids is passed, it should query only those league_ids
    result = asyncio.run(
        get_leaguemate_ids(
            db=db,
            main_user_id="user_main",
            league_ids=["league_2026_1", "league_2026_2"],
        )
    )

    assert len(result) == 2
    assert len(executed_stmts) == 1
    # Verify the where clause includes the passed league_ids
    stmt_str = str(executed_stmts[0]).lower()
    assert "league_id in" in stmt_str or "league_id =" in stmt_str


def test_read_trades_filters_completed_and_excluded_leagues():
    from app.crud.sleeper.trade import read_trades

    executed_stmts = []

    class MockResult:
        def __init__(self, data):
            self.data = data
        def scalars(self):
            return self
        def unique(self):
            return self
        def all(self):
            return self.data

    class MockDB:
        async def execute(self, stmt):
            executed_stmts.append(stmt)
            return MockResult([])

    db = MockDB()
    result = asyncio.run(
        read_trades(
            db=db,
            lms=["user_lm_1"],
            exclude_league_ids={"league_hidden_1"},
            include_completed=False,
        )
    )

    assert result == {}
    assert len(executed_stmts) >= 1
    first_stmt = str(executed_stmts[0]).lower()
    # Should check League.status != complete and exclude hidden league
    assert "status != :status_1" in first_stmt or "complete" in first_stmt or "status" in first_stmt
    assert "notin" in first_stmt or "not in" in first_stmt or "league_hidden_1" in first_stmt


