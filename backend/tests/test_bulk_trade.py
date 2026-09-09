from types import SimpleNamespace

from app.schemas.trades import TradeDraftPickAsset
from app.services.trades.bulk import get_counterparty_options


def _pick(
    *,
    season: str,
    round_number: int,
    og_roster_id: int,
    current_owner_roster_id: int,
    label: str,
) -> TradeDraftPickAsset:
    return TradeDraftPickAsset(
        season=season,
        round=round_number,
        og_roster_id=og_roster_id,
        current_owner_roster_id=current_owner_roster_id,
        label=label,
    )


def test_get_counterparty_options_requires_full_pick_package():
    league_rosters = [
        SimpleNamespace(roster_id=1, owner_id="you"),
        SimpleNamespace(roster_id=2, owner_id="alpha"),
        SimpleNamespace(roster_id=3, owner_id="beta"),
    ]
    pick_assets = [
        _pick(
            season="2027",
            round_number=1,
            og_roster_id=2,
            current_owner_roster_id=2,
            label="2027 Pick 1.02",
        ),
        _pick(
            season="2027",
            round_number=2,
            og_roster_id=2,
            current_owner_roster_id=2,
            label="2027 Pick 2.02",
        ),
        _pick(
            season="2027",
            round_number=1,
            og_roster_id=3,
            current_owner_roster_id=3,
            label="2027 Pick 1.03",
        ),
    ]

    counterparties = get_counterparty_options(
        your_roster_id=1,
        league_rosters=league_rosters,
        pick_assets=pick_assets,
        requested_picks=[
            SimpleNamespace(season="2027", round=1),
            SimpleNamespace(season="2027", round=2),
        ],
        user_names_by_id={
            "alpha": "Alpha",
            "beta": "Beta",
        },
    )

    assert [counterparty.roster_id for counterparty in counterparties] == [2]
    assert len(counterparties[0].pick_choices) == 2
    assert counterparties[0].pick_choices[0].matching_picks[0].label == "2027 Pick 1.02"
    assert counterparties[0].pick_choices[1].matching_picks[0].label == "2027 Pick 2.02"


def test_get_counterparty_options_keeps_pick_choices_split_by_request():
    league_rosters = [
        SimpleNamespace(roster_id=1, owner_id="you"),
        SimpleNamespace(roster_id=4, owner_id="gamma"),
    ]
    pick_assets = [
        _pick(
            season="2028",
            round_number=1,
            og_roster_id=4,
            current_owner_roster_id=4,
            label="2028 Pick 1.04",
        ),
        _pick(
            season="2028",
            round_number=1,
            og_roster_id=7,
            current_owner_roster_id=4,
            label="2028 Pick 1.07",
        ),
        _pick(
            season="2028",
            round_number=2,
            og_roster_id=4,
            current_owner_roster_id=4,
            label="2028 Pick 2.04",
        ),
    ]

    counterparties = get_counterparty_options(
        your_roster_id=1,
        league_rosters=league_rosters,
        pick_assets=pick_assets,
        requested_picks=[
            SimpleNamespace(season="2028", round=1),
            SimpleNamespace(season="2028", round=2),
        ],
        user_names_by_id={
            "gamma": "Gamma",
        },
    )

    assert len(counterparties) == 1
    assert counterparties[0].name == "Gamma"
    assert counterparties[0].pick_choices[0].request_index == 0
    assert [pick.label for pick in counterparties[0].pick_choices[0].matching_picks] == [
        "2028 Pick 1.04",
        "2028 Pick 1.07",
    ]
    assert counterparties[0].pick_choices[1].request_index == 1
    assert [pick.label for pick in counterparties[0].pick_choices[1].matching_picks] == [
        "2028 Pick 2.04",
    ]


import asyncio
import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, MagicMock

from app.models.db.sleeper.connection import SleeperConnection
from app.models.db.sleeper.api import League, Roster
from app.schemas.trades import BulkTradeOfferRequest
from app.services.trades.bulk import validate_and_build_trade_variables


def _build_test_roster(roster_id: int, owner_id: str, players: list[str], waiver_budget_used: int = 0) -> Roster:
    return Roster(
        roster_id=roster_id,
        owner_id=owner_id,
        league_id="league_1",
        players=players,
        settings={"waiver_budget_used": waiver_budget_used},
    )


def _build_test_league(waiver_budget: int = 100) -> League:
    return League(
        league_id="league_1",
        name="Test League",
        settings={"waiver_budget": waiver_budget},
    )


def test_validate_and_build_trade_variables_faab_success(monkeypatch):
    your_roster = _build_test_roster(1, "my_user", ["p_send"], waiver_budget_used=20)
    counterparty_roster = _build_test_roster(2, "other_user", ["p_recv"], waiver_budget_used=50)
    league = _build_test_league(waiver_budget=100)

    # Available: your_roster = 80, counterparty = 50
    offer = BulkTradeOfferRequest(
        league_id="league_1",
        your_roster_id=1,
        counterparty_roster_id=2,
        send_player_ids=["p_send"],
        receive_player_ids=["p_recv"],
        send_faab=15,
        receive_faab=25,
    )

    db = AsyncMock()
    # 1st execute: owned_row
    first_result = MagicMock()
    first_result.one_or_none.return_value = (your_roster, league)

    # 2nd execute: league rosters
    second_result = MagicMock()
    second_result.scalars.return_value = [your_roster, counterparty_roster]

    db.execute.side_effect = [first_result, second_result]

    monkeypatch.setattr(
        "app.services.trades.bulk.get_user_names_by_id",
        AsyncMock(return_value={"my_user": "Me", "other_user": "Them"}),
    )
    monkeypatch.setattr(
        "app.services.trades.bulk.get_current_pick_assets_by_league",
        AsyncMock(return_value={}),
    )

    connection = SleeperConnection(sleeper_user_id="my_user")
    sleeper = MagicMock()

    variables = asyncio.run(
        validate_and_build_trade_variables(
            db=db,
            connection=connection,
            sleeper=sleeper,
            offer=offer,
        )
    )

    assert variables["waiver_budget"] == ["1,2,15", "2,1,25"]
    assert variables["league_id"] == "league_1"
    assert variables["k_adds"] == ["p_send", "p_recv"]


def test_validate_and_build_trade_variables_send_faab_exceeded(monkeypatch):
    your_roster = _build_test_roster(1, "my_user", ["p_send"], waiver_budget_used=90)
    counterparty_roster = _build_test_roster(2, "other_user", ["p_recv"], waiver_budget_used=10)
    league = _build_test_league(waiver_budget=100)

    # Available: your_roster = 10, but offer sends 20
    offer = BulkTradeOfferRequest(
        league_id="league_1",
        your_roster_id=1,
        counterparty_roster_id=2,
        send_player_ids=["p_send"],
        receive_player_ids=["p_recv"],
        send_faab=20,
        receive_faab=0,
    )

    db = AsyncMock()
    first_result = MagicMock()
    first_result.one_or_none.return_value = (your_roster, league)
    second_result = MagicMock()
    second_result.scalars.return_value = [your_roster, counterparty_roster]
    db.execute.side_effect = [first_result, second_result]

    monkeypatch.setattr(
        "app.services.trades.bulk.get_user_names_by_id",
        AsyncMock(return_value={}),
    )
    monkeypatch.setattr(
        "app.services.trades.bulk.get_current_pick_assets_by_league",
        AsyncMock(return_value={}),
    )

    connection = SleeperConnection(sleeper_user_id="my_user")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            validate_and_build_trade_variables(
                db=db,
                connection=connection,
                sleeper=MagicMock(),
                offer=offer,
            )
        )
    assert exc_info.value.status_code == 400
    assert "You do not have enough FAAB available" in exc_info.value.detail


def test_validate_and_build_trade_variables_receive_faab_exceeded(monkeypatch):
    your_roster = _build_test_roster(1, "my_user", ["p_send"], waiver_budget_used=10)
    counterparty_roster = _build_test_roster(2, "other_user", ["p_recv"], waiver_budget_used=95)
    league = _build_test_league(waiver_budget=100)

    # Available: counterparty = 5, but offer asks for 10
    offer = BulkTradeOfferRequest(
        league_id="league_1",
        your_roster_id=1,
        counterparty_roster_id=2,
        send_player_ids=["p_send"],
        receive_player_ids=["p_recv"],
        send_faab=0,
        receive_faab=10,
    )

    db = AsyncMock()
    first_result = MagicMock()
    first_result.one_or_none.return_value = (your_roster, league)
    second_result = MagicMock()
    second_result.scalars.return_value = [your_roster, counterparty_roster]
    db.execute.side_effect = [first_result, second_result]

    monkeypatch.setattr(
        "app.services.trades.bulk.get_user_names_by_id",
        AsyncMock(return_value={}),
    )
    monkeypatch.setattr(
        "app.services.trades.bulk.get_current_pick_assets_by_league",
        AsyncMock(return_value={}),
    )

    connection = SleeperConnection(sleeper_user_id="my_user")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            validate_and_build_trade_variables(
                db=db,
                connection=connection,
                sleeper=MagicMock(),
                offer=offer,
            )
        )
    assert exc_info.value.status_code == 400
    assert "The counterparty does not have enough FAAB available" in exc_info.value.detail

