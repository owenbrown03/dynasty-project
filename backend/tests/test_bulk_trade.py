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
