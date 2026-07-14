import asyncio
from types import SimpleNamespace

from app.crud.sleeper import league as league_crud


class FakeScalarResult:
    def all(self):
        return []


class FakeExecuteResult:
    def scalars(self):
        return FakeScalarResult()


class FakeDB:
    def __init__(self):
        self.insert_statements = []

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
