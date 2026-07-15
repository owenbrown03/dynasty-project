import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.crud.sleeper import league as league_crud
from app.services.waivers import recent_drops as recent_drops_service


class FakeScalarResult:
    def all(self):
        return []


class FakeExecuteResult:
    def scalars(self):
        return FakeScalarResult()


class FakeDB:
    def __init__(self):
        self.insert_statements = []
        self.commit_calls = 0

    async def execute(self, statement):
        table = getattr(
            statement,
            "table",
            None,
        )
        if table is not None:
            self.insert_statements.append(
                (
                    table.name,
                    statement.compile().params,
                )
            )
        return FakeExecuteResult()

    async def commit(self):
        self.commit_calls += 1


def test_save_transactions_persists_drop_transactions(
    monkeypatch,
):
    db = FakeDB()
    upsert_calls = []

    async def fake_bulk_upsert(
        db,
        model,
        values,
        pk_field,
    ):
        del db, model, pk_field
        upsert_calls.append(values)

    monkeypatch.setattr(
        league_crud,
        "_bulk_upsert",
        fake_bulk_upsert,
    )

    transaction = SimpleNamespace(
        transaction_id="txn-drop-1",
        type="waiver",
        status="complete",
        status_updated=123456789,
        adds={},
        drops={"player-1": 9},
        waiver_budget=[],
        draft_picks=[],
    )

    asyncio.run(
        league_crud._save_transactions(
            db=db,
            transactions=[transaction],
            league_id="league-1",
        )
    )

    assert upsert_calls == [[
        {
            "transaction_id": "txn-drop-1",
            "type": "waiver",
            "status": "complete",
            "time_ms": 123456789,
            "league_id": "league-1",
        }
    ]]
    assert db.insert_statements == [
        (
            "movement",
            {
                "transaction_id_m0": "txn-drop-1",
                "player_id_m0": "player-1",
                "roster_id_m0": 9,
                "action_m0": "DROP",
            },
        )
    ]


def test_needs_recent_activity_sync_uses_short_freshness_window():
    now = datetime.now(UTC)

    assert league_crud.needs_recent_activity_sync(None, now=now) is True
    assert (
        league_crud.needs_recent_activity_sync(
            SimpleNamespace(last_synced_at=None),
            now=now,
        )
        is True
    )
    assert (
        league_crud.needs_recent_activity_sync(
            SimpleNamespace(
                last_synced_at=now - timedelta(minutes=20),
            ),
            now=now,
        )
        is True
    )
    assert (
        league_crud.needs_recent_activity_sync(
            SimpleNamespace(
                last_synced_at=now - timedelta(minutes=5),
            ),
            now=now,
        )
        is False
    )


def test_sync_transactions_for_known_leagues_fetches_recent_weeks(
    monkeypatch,
):
    db = FakeDB()
    saved_transactions = []
    updated_bundles = []

    async def fake_get_sync_states(db, league_ids):
        del db
        return {
            league_id: SimpleNamespace(last_synced_week=2)
            for league_id in league_ids
        }

    async def fake_save_transactions(db, transactions, league_id):
        del db
        saved_transactions.append(
            {
                "league_id": league_id,
                "transaction_ids": [
                    transaction.transaction_id
                    for transaction in transactions
                ],
            }
        )

    async def fake_update_sync_states(*, db, bundles):
        del db
        updated_bundles.extend(bundles)

    monkeypatch.setattr(
        league_crud,
        "get_sync_states",
        fake_get_sync_states,
    )
    monkeypatch.setattr(
        league_crud,
        "_save_transactions",
        fake_save_transactions,
    )
    monkeypatch.setattr(
        league_crud,
        "_update_sync_states",
        fake_update_sync_states,
    )

    requested = []

    class FakeSleeper:
        class read:
            @staticmethod
            async def get_transactions(league_id, week):
                requested.append((league_id, week))
                return [
                    SimpleNamespace(
                        transaction_id=f"{league_id}-{week}",
                    )
                ]

    result = asyncio.run(
        league_crud.sync_transactions_for_known_leagues(
            db=db,
            leagues=[
                SimpleNamespace(league_id="league-1"),
            ],
            curr_week=4,
            sleeper=FakeSleeper(),
        )
    )

    assert requested == [
        ("league-1", 3),
        ("league-1", 4),
    ]
    assert saved_transactions == [
        {
            "league_id": "league-1",
            "transaction_ids": ["league-1-3", "league-1-4"],
        }
    ]
    assert updated_bundles == [
        {
            "league_id": "league-1",
            "synced_week": 4,
            "transactions_only": True,
        }
    ]
    assert result == {"league-1": 4}
    assert db.commit_calls == 1


def test_sync_recent_drop_activity_only_syncs_stale_visible_leagues(
    monkeypatch,
):
    league_fresh = SimpleNamespace(league_id="fresh")
    league_stale = SimpleNamespace(league_id="stale")
    connection = SimpleNamespace(
        sleeper_user_id="sleeper-1",
        site_user_id=None,
    )

    async def fake_visible_rows(
        *,
        db,
        sleeper_user_id,
        site_user_id,
    ):
        del db, sleeper_user_id, site_user_id
        return [
            SimpleNamespace(league=league_fresh),
            SimpleNamespace(league=league_stale),
        ]

    now = datetime.now(UTC)

    async def fake_get_sync_states(db, league_ids):
        del db, league_ids
        return {
            "fresh": SimpleNamespace(last_synced_at=now),
            "stale": SimpleNamespace(
                last_synced_at=now - timedelta(minutes=30),
            ),
        }

    synced = []

    async def fake_sync_transactions_for_known_leagues(
        *,
        db,
        leagues,
        curr_week,
        sleeper,
    ):
        del db, sleeper
        synced.append(
            {
                "league_ids": [league.league_id for league in leagues],
                "curr_week": curr_week,
            }
        )
        return {"stale": curr_week}

    class FakeSleeper:
        class read:
            @staticmethod
            async def get_nfl_state():
                return SimpleNamespace(week="3")

    monkeypatch.setattr(
        recent_drops_service,
        "get_visible_owned_league_rows_by_sleeper_user_id",
        fake_visible_rows,
    )
    monkeypatch.setattr(
        recent_drops_service,
        "get_sync_states",
        fake_get_sync_states,
    )
    monkeypatch.setattr(
        recent_drops_service,
        "sync_transactions_for_known_leagues",
        fake_sync_transactions_for_known_leagues,
    )

    synced_result = asyncio.run(
        recent_drops_service.sync_recent_drop_activity(
            db=FakeDB(),
            sleeper=FakeSleeper(),
            connection=connection,
        )
    )

    assert synced_result is True
    assert synced == [
        {
            "league_ids": ["stale"],
            "curr_week": 3,
        }
    ]
