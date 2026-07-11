import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.crud.sleeper import league as league_crud


class FakeNestedTransaction:
    def __init__(self, db):
        self.db = db

    async def __aenter__(self):
        self.db.nested_entries += 1
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type is None:
            self.db.nested_commits += 1
        else:
            self.db.nested_rollbacks += 1

        return False


class FakeDB:
    def __init__(self):
        self.nested_entries = 0
        self.nested_commits = 0
        self.nested_rollbacks = 0
        self.flush_calls = 0
        self.commit_calls = 0

    def begin_nested(self):
        return FakeNestedTransaction(self)

    async def flush(self):
        self.flush_calls += 1

    async def commit(self):
        self.commit_calls += 1


def test_was_synced_today_uses_calendar_day():
    assert league_crud.was_synced_today(None) is False
    assert (
        league_crud.was_synced_today(
            SimpleNamespace(last_synced_at=None)
        )
        is False
    )


def test_needs_full_refresh_uses_last_full_sync_age():
    assert league_crud.needs_full_refresh(None) is True
    assert (
        league_crud.needs_full_refresh(
            SimpleNamespace(last_full_synced_at=None)
        )
        is True
    )
    assert (
        league_crud.needs_full_refresh(
            SimpleNamespace(
                last_full_synced_at=datetime.now()
                - timedelta(days=1),
            )
        )
        is False
    )
    assert (
        league_crud.needs_full_refresh(
            SimpleNamespace(
                last_full_synced_at=datetime.now()
                - timedelta(
                    days=league_crud.FULL_REFRESH_INTERVAL_DAYS + 1,
                ),
            )
        )
        is True
    )
    assert (
        league_crud.was_synced_today(
            SimpleNamespace(
                last_synced_at=datetime.now(UTC),
            )
        )
        is True
    )
    assert (
        league_crud.was_synced_today(
            SimpleNamespace(
                last_synced_at=datetime.now(UTC)
                - timedelta(days=1),
            )
        )
        is False
    )


def test_sync_leagues_uses_nested_transaction_per_batch(
    monkeypatch,
):
    db = FakeDB()
    update_calls: list[list[dict]] = []

    async def fake_get_existing_leagues(db, league_ids):
        return set()

    async def fake_get_sync_states(db, league_ids):
        return {}

    async def fake_get_incomplete_league_ids(db, league_ids):
        return set()

    async def fake_fetch_league_bundle(
        *,
        league,
        curr_week,
        sleeper,
        existing_ids,
        sync_states,
        incomplete_league_ids,
        force=False,
        existing_refresh="full",
    ):
        del incomplete_league_ids
        return {"league_id": league.league_id}

    async def fake_bounded_gather(
        coros,
        **kwargs,
    ):
        del kwargs
        return [await coro for coro in coros]

    async def fake_save_league_bundle_to_db(
        db,
        bundle,
        commit=True,
    ):
        return bundle["league_id"] != "league-2"

    async def fake_update_sync_states(*, db, bundles):
        update_calls.append(bundles)

    monkeypatch.setattr(
        league_crud,
        "get_existing_leagues",
        fake_get_existing_leagues,
    )
    monkeypatch.setattr(
        league_crud,
        "get_sync_states",
        fake_get_sync_states,
    )
    monkeypatch.setattr(
        league_crud,
        "fetch_league_bundle",
        fake_fetch_league_bundle,
    )
    monkeypatch.setattr(
        league_crud,
        "get_incomplete_league_ids",
        fake_get_incomplete_league_ids,
    )
    monkeypatch.setattr(
        league_crud,
        "bounded_gather",
        fake_bounded_gather,
    )
    monkeypatch.setattr(
        league_crud,
        "save_league_bundle_to_db",
        fake_save_league_bundle_to_db,
    )
    monkeypatch.setattr(
        league_crud,
        "_update_sync_states",
        fake_update_sync_states,
    )

    result = asyncio.run(
        league_crud.sync_leagues(
            db=db,
            raw_leagues=[
                SimpleNamespace(league_id="league-1"),
                SimpleNamespace(league_id="league-2"),
            ],
            curr_week=1,
            sleeper=object(),
        )
    )

    assert result == {
        "status": "completed",
        "synced_count": 0,
        "failed_batches": 1,
    }
    assert db.nested_entries == 1
    assert db.nested_rollbacks == 1
    assert db.nested_commits == 0
    assert db.flush_calls == 0
    assert db.commit_calls == 1
    assert update_calls == []


def test_fetch_league_bundle_uses_transactions_only_for_existing_league():
    class FakeRead:
        def __init__(self):
            self.calls: list[tuple[str, str, int | None]] = []

        async def get_transactions(
            self,
            league_id,
            week,
        ):
            self.calls.append(
                ("get_transactions", league_id, week)
            )
            return [
                SimpleNamespace(
                    transaction_id=f"{league_id}-{week}",
                    type="trade",
                )
            ]

        async def get_league(self, league_id):
            self.calls.append(
                ("get_league", league_id, None)
            )
            return SimpleNamespace()

        async def get_users(self, league_id):
            self.calls.append(
                ("get_users", league_id, None)
            )
            return []

        async def get_rosters(self, league_id):
            self.calls.append(
                ("get_rosters", league_id, None)
            )
            return []

        async def get_drafts_league(self, league_id):
            self.calls.append(
                ("get_drafts_league", league_id, None)
            )
            return []

    sleeper = SimpleNamespace(
        read=FakeRead(),
    )

    bundle = asyncio.run(
        league_crud.fetch_league_bundle(
            league=SimpleNamespace(
                league_id="league-1",
            ),
            curr_week=3,
            sleeper=sleeper,
            existing_ids={"league-1"},
            sync_states={
                "league-1": SimpleNamespace(
                    last_synced_week=1,
                    last_synced_at=None,
                    last_full_synced_at=datetime.now(),
                )
            },
            incomplete_league_ids=set(),
            existing_refresh="transactions_only",
        )
    )

    assert bundle == {
        "league_id": "league-1",
        "transactions": [
            SimpleNamespace(
                transaction_id="league-1-2",
                type="trade",
            ),
            SimpleNamespace(
                transaction_id="league-1-3",
                type="trade",
            ),
        ],
        "transactions_only": True,
        "synced_week": 3,
    }
    assert sleeper.read.calls == [
        ("get_transactions", "league-1", 2),
        ("get_transactions", "league-1", 3),
    ]


def test_fetch_league_bundle_uses_full_refresh_for_incomplete_existing_league():
    class FakeRead:
        def __init__(self):
            self.calls: list[tuple[str, str, int | None]] = []

        async def get_transactions(self, league_id, week):
            self.calls.append(
                ("get_transactions", league_id, week)
            )
            return []

        async def get_league(self, league_id):
            self.calls.append(
                ("get_league", league_id, None)
            )
            return SimpleNamespace(league_id=league_id)

        async def get_users(self, league_id):
            self.calls.append(
                ("get_users", league_id, None)
            )
            return []

        async def get_rosters(self, league_id):
            self.calls.append(
                ("get_rosters", league_id, None)
            )
            return []

        async def get_drafts_league(self, league_id):
            self.calls.append(
                ("get_drafts_league", league_id, None)
            )
            return []

    sleeper = SimpleNamespace(
        read=FakeRead(),
    )

    bundle = asyncio.run(
        league_crud.fetch_league_bundle(
            league=SimpleNamespace(
                league_id="league-1",
            ),
            curr_week=3,
            sleeper=sleeper,
            existing_ids={"league-1"},
            sync_states={
                "league-1": SimpleNamespace(
                    last_synced_week=1,
                    last_synced_at=datetime.now(),
                    last_full_synced_at=datetime.now(),
                )
            },
            incomplete_league_ids={"league-1"},
            existing_refresh="transactions_only",
        )
    )

    assert bundle is not None
    assert bundle["transactions_only"] is False
    assert ("get_league", "league-1", None) in sleeper.read.calls
    assert ("get_users", "league-1", None) in sleeper.read.calls
    assert ("get_rosters", "league-1", None) in sleeper.read.calls
    assert ("get_drafts_league", "league-1", None) in sleeper.read.calls
