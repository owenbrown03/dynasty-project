from types import SimpleNamespace

from app.services.advisor.candidates import (
    COUNTERPARTY_MARKET_MAX_RATIO,
    COUNTERPARTY_MARKET_MIN_RATIO,
    PickAsset,
    _fix_with_extra_receive_pick,
    _match_package,
    _passes_value_constraints,
)


def _item(player_id: str, ktc: float, personal_war: float):
    return SimpleNamespace(
        player=SimpleNamespace(
            player_id=player_id,
            fc_value=ktc,
        ),
        custom_values=SimpleNamespace(
            dynasty_roster_war=personal_war,
            redraft_roster_war=None,
        ),
    )


def _pick(
    og: int,
    season: str = "2027",
    round_: int = 1,
    value: float = 500.0,
    war_value: float | None = None,
):
    return PickAsset(
        season=season,
        round=round_,
        og_roster_id=og,
        owner_roster_id=og,
        value=value,
        war_value=war_value
        if war_value is not None
        else value / 250.0,
    )


def _personal_war(item):
    return item.custom_values.dynasty_roster_war


def test_match_package_rejects_underpay():
    sell_pool = [_item("a", 800.0, 1.0)]

    players, picks = _match_package(
        sell_pool,
        [],
        target_market=2000.0,
    )

    assert players is None
    assert picks == []


def test_match_package_prefers_smallest_convincing_ratio():
    sell_pool = [
        _item("overpay", 2600.0, 1.0),
        _item("even", 2100.0, 1.0),
    ]

    players, picks = _match_package(
        sell_pool,
        [],
        target_market=2000.0,
    )

    assert [i.player.player_id for i in players] == ["even"]
    assert picks == []


def test_match_package_pair_fallback_within_band():
    sell_pool = [
        _item("a", 1200.0, 1.0),
        _item("b", 1100.0, 1.0),
    ]

    players, picks = _match_package(
        sell_pool,
        [],
        target_market=1500.0,
    )

    assert picks == []
    ratio = sum(i.player.fc_value for i in players) / 1500.0
    assert COUNTERPARTY_MARKET_MIN_RATIO <= ratio
    assert ratio <= COUNTERPARTY_MARKET_MAX_RATIO


def test_match_package_respects_used_ids():
    used = {"even"}
    sell_pool = [
        _item("even", 2100.0, 1.0),
        _item("other", 2400.0, 1.0),
    ]

    players, picks = _match_package(
        sell_pool,
        [],
        target_market=2000.0,
        used_player_ids=used,
    )

    assert [i.player.player_id for i in players] == ["other"]
    assert picks == []


def test_match_package_player_plus_pick_tier():
    sell_pool = [_item("small", 900.0, 1.0)]

    players, picks = _match_package(
        sell_pool,
        [_pick(4, round_=2, value=400.0)],
        target_market=1000.0,
    )

    assert [i.player.player_id for i in players] == ["small"]
    assert [p.round for p in picks] == [2]


def test_match_package_pick_only_tier():
    sell_pool = []

    players, picks = _match_package(
        sell_pool,
        [_pick(6, round_=1, value=2200.0)],
        target_market=2000.0,
    )

    assert players == []
    assert [p.round for p in picks] == [1]


def test_fix_with_extra_receive_pick_flips_personal_loss():
    # We overpay 1.3x market and are still personally underwater;
    # one small counterparty pick closes the personal gap while the
    # ratio stays inside the convincing band.
    sweetener = _fix_with_extra_receive_pick(
        their_picks=[_pick(9, round_=3, value=300.0)],
        market_send_total=1300.0,
        market_receive_total=1000.0,
        personal_send_total=1.5,
        personal_receive_total=1.3,
    )

    assert sweetener is not None
    assert sweetener.value == 300.0


def test_fix_with_extra_receive_pick_rejects_when_ratio_floors():
    # Adding the pick would push the counterparty's gain below the
    # minimum convincing ratio, so no sweetener may be used.
    sweetener = _fix_with_extra_receive_pick(
        their_picks=[_pick(9, round_=3, value=50.0)],
        market_send_total=1000.0,
        market_receive_total=995.0,
        personal_send_total=1.5,
        personal_receive_total=1.3,
    )

    assert sweetener is None


def test_value_constraints_accept_counterparty_win_and_personal_win():
    assert _passes_value_constraints(
        market_send_total=2300.0,
        market_receive_total=2000.0,
        personal_send_total=1.0,
        personal_receive_total=2.5,
    )


def test_value_constraints_accept_ties():
    assert _passes_value_constraints(
        market_send_total=2000.0,
        market_receive_total=2000.0,
        personal_send_total=2.0,
        personal_receive_total=2.0,
    )


def test_value_constraints_reject_counterparty_loss():
    assert not _passes_value_constraints(
        market_send_total=1800.0,
        market_receive_total=2000.0,
        personal_send_total=1.0,
        personal_receive_total=3.0,
    )


def test_value_constraints_reject_personal_loss():
    assert not _passes_value_constraints(
        market_send_total=2300.0,
        market_receive_total=2000.0,
        personal_send_total=3.0,
        personal_receive_total=2.5,
    )


def test_value_constraints_reject_missing_personal_values():
    assert not _passes_value_constraints(
        market_send_total=2300.0,
        market_receive_total=2000.0,
        personal_send_total=None,
        personal_receive_total=2.5,
    )
