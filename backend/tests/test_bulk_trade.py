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


def test_build_pick_label_with_projected_slot():
    from app.services.trades.picks import build_pick_label

    # Next-year pick with projected slot - original owner
    label_orig = build_pick_label(
        season="2027",
        round_number=1,
        og_roster_id=2,
        current_owner_roster_id=2,
        roster_name_by_id={2: "browntown333"},
        projected_slot=4,
        is_projected=True,
    )
    assert label_orig == "2027 Pick 1.04 (proj.) (browntown333's original)"

    # Next-year pick with projected slot - acquired pick
    label_acquired = build_pick_label(
        season="2027",
        round_number=1,
        og_roster_id=3,
        current_owner_roster_id=2,
        roster_name_by_id={3: "Darven"},
        projected_slot=9,
        is_projected=True,
    )
    assert label_acquired == "2027 Pick 1.09 (proj.) (from Darven)"

    # Future pick beyond next year (no projection)
    label_future = build_pick_label(
        season="2028",
        round_number=2,
        og_roster_id=2,
        current_owner_roster_id=2,
        roster_name_by_id={2: "browntown333"},
    )
    assert label_future == "2028 Round 2 (browntown333's original)"

    # Fixed slot (e.g. current year draft order set)
    label_fixed = build_pick_label(
        season="2026",
        round_number=1,
        og_roster_id=2,
        current_owner_roster_id=2,
        roster_name_by_id={2: "browntown333"},
        slot=3,
    )
    assert label_fixed == "2026 Pick 1.03 (browntown333's original)"


def test_get_current_pick_assets_by_league_with_projected_slots():
    from app.services.trades.picks import get_current_pick_assets_by_league

    sleeper = MagicMock()
    sleeper.read.get_traded_picks = AsyncMock(return_value=[])

    roster1 = SimpleNamespace(roster_id=1, owner_id="user1")
    roster2 = SimpleNamespace(roster_id=2, owner_id="user2")

    res = asyncio.run(
        get_current_pick_assets_by_league(
            sleeper=sleeper,
            rosters_by_league_id={"league_1": [roster1, roster2]},
            requested_picks=[("2027", 1)],
            roster_names_by_league_id={"league_1": {1: "Team 1", 2: "Team 2"}},
            projected_slots_by_league={
                "league_1": {
                    ("2027", 1): 2,
                    ("2027", 2): 7,
                }
            },
        )
    )

    picks = res["league_1"]
    assert len(picks) == 2
    assert picks[0].og_roster_id == 1
    assert picks[0].projected_slot == 2
    assert picks[0].label == "2027 Pick 1.02 (proj.) (Team 1's original)"
    assert picks[1].og_roster_id == 2
    assert picks[1].projected_slot == 7
    assert picks[1].label == "2027 Pick 1.07 (proj.) (Team 2's original)"


def test_bulk_trade_drop_candidates_calculation(monkeypatch):
    import app.services.trades.bulk as bulk_mod
    from app.schemas.trades import BulkTradePickRequest

    db = MagicMock()
    sleeper = MagicMock()
    sleeper.read.get_traded_picks = AsyncMock(return_value=[])

    connection = SimpleNamespace(
        sleeper_user_id="user_me",
        sleeper_username="browntown",
        site_user_id="site_1",
    )

    class FakeRoster:
        def __init__(self):
            self.roster_id = 1
            self.owner_id = "user_me"
            self.players = ["p1", "p2", "p3"]
            self.reserve = []
            self.taxi = []
            self.settings = {"total_moves": 0}

        def open_roster_spots(self, league):
            return 0

        def faab_remaining(self, league):
            return 100

    class FakeLeague:
        def __init__(self):
            self.league_id = "l1"
            self.name = "Test League"
            self.avatar = None
            self.roster_positions = ["QB", "RB", "WR", "TE", "SUPER_FLEX"]
            self.is_best_ball = False
            self.status = "in_season"
            self.season = "2026"

    owned_row = SimpleNamespace(roster=FakeRoster(), league=FakeLeague())
    roster2 = SimpleNamespace(
        roster_id=2,
        owner_id="user_other",
        players=["p_target"],
        reserve=[],
        taxi=[],
        faab_remaining=lambda league: 50,
    )

    p_target = SimpleNamespace(
        player_id="p_target",
        position="RB",
        full_name="Target Player",
        team="SF",
        birth_date=None,
    )
    monkeypatch.setattr(bulk_mod, "get_bulk_trade_target_players", AsyncMock(return_value=[p_target]))
    monkeypatch.setattr(bulk_mod, "get_visible_owned_league_rows_by_sleeper_user_id", AsyncMock(return_value=[owned_row]))
    monkeypatch.setattr(bulk_mod, "get_all_rosters_by_league", AsyncMock(return_value={"l1": [owned_row.roster, roster2]}))
    monkeypatch.setattr(bulk_mod, "get_user_names_by_id", AsyncMock(return_value={"user_other": "Other Manager"}))
    monkeypatch.setattr(
        bulk_mod,
        "get_current_pick_assets_by_league",
        AsyncMock(return_value={"l1": [
            _pick(
                season="2027",
                round_number=1,
                og_roster_id=1,
                current_owner_roster_id=1,
                label="2027 Pick 1.01",
            )
        ]}),
    )

    p1 = SimpleNamespace(player_id="p1", full_name="Player One", position="RB", team="NYG")
    p2 = SimpleNamespace(player_id="p2", full_name="Player Two", position="WR", team="DAL")
    p3 = SimpleNamespace(player_id="p3", full_name="Player Three", position="TE", team="KC")

    k1 = SimpleNamespace(player_id="p1", sf_value=100.0, value=100.0)
    k2 = SimpleNamespace(player_id="p2", sf_value=500.0, value=500.0)
    k3 = SimpleNamespace(player_id="p3", sf_value=50.0, value=50.0)

    result_p = MagicMock()
    result_p.scalars.return_value.all.return_value = [p1, p2, p3]

    result_k = MagicMock()
    result_k.scalars.return_value.all.return_value = [k1, k2, k3]

    def side_effect_exec(statement, *args, **kwargs):
        stmt_str = str(statement).lower()
        if "ktc" in stmt_str or "ktc_values" in stmt_str:
            return result_k
        if "players" in stmt_str or "player" in stmt_str:
            return result_p
        mock_empty = MagicMock()
        mock_empty.scalars.return_value.all.return_value = []
        mock_empty.all.return_value = []
        return mock_empty

    db.execute = AsyncMock(side_effect=side_effect_exec)

    # Receiving 1 player (target), sending 0 players + 1 pick
    resp = asyncio.run(
        bulk_mod.get_bulk_trade_availability(
            db=db,
            connection=connection,
            sleeper=sleeper,
            send_player_ids=[],
            send_picks=[BulkTradePickRequest(season="2027", round=1)],
            receive_player_ids=["p_target"],
            receive_picks=[],
        )
    )

    assert len(resp.leagues) == 1
    avail = resp.leagues[0]
    assert avail.open_roster_spots == 0
    assert avail.needed_drops == 1
    assert len(avail.drop_candidates) == 1
    # Lowest value was p3 (sf_value 50)
    assert avail.drop_candidates[0].player_id == "p3"
    assert avail.drop_candidates[0].name == "Player Three"
    assert avail.drop_candidates[0].value == 50.0




