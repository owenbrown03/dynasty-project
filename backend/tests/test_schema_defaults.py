from app.integrations.sleeper.schemas.api import (
    Draft,
    Transaction,
)
from app.integrations.sleeper.schemas.display import (
    Movement,
    Transaction as DisplayTransaction,
    User,
)
from app.integrations.sleeper.types import TradeRequest


def test_trade_request_uses_isolated_list_defaults():
    first = TradeRequest(league_id="1")
    second = TradeRequest(league_id="2")

    first.k_adds.append("player-1")

    assert second.k_adds == []


def test_sleeper_api_models_use_isolated_collection_defaults():
    first = Transaction(
        transaction_id="txn-1",
        status_updated=1,
        type="trade",
    )
    second = Transaction(
        transaction_id="txn-2",
        status_updated=2,
        type="trade",
    )

    first.roster_ids.append(1)
    first.waiver_budget.append(
        {"sender": 1, "receiver": 2, "amount": 10},
    )
    first.draft_picks.append(
        {
            "season": "2027",
            "round": 1,
            "roster_id": 1,
            "previous_owner_id": 2,
            "owner_id": 3,
        },
    )

    assert second.roster_ids == []
    assert second.waiver_budget == []
    assert second.draft_picks == []

    first_draft = Draft(
        draft_id="draft-1",
        league_id="league-1",
        season="2027",
    )
    second_draft = Draft(
        draft_id="draft-2",
        league_id="league-2",
        season="2028",
    )

    first_draft.draft_order["1"] = 1

    assert second_draft.draft_order == {}


def test_display_models_use_isolated_list_defaults():
    first = User(
        display_name="One",
    )
    second = User(
        display_name="Two",
    )

    first.adds.append(
        Movement(name="Asset"),
    )

    assert second.adds == []

    display_txn = DisplayTransaction(
        transaction_id="txn",
        time_ms=1,
        league_name="League",
    )

    assert display_txn.users == []
