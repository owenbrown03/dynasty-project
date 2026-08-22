from types import SimpleNamespace

from app.services.advisor.candidates import (
    COUNTERPARTY_KTC_MAX_RATIO,
    COUNTERPARTY_KTC_MIN_RATIO,
    _match_package,
    _passes_value_constraints,
)


def _item(player_id: str, ktc: float, personal_war: float):
    return SimpleNamespace(
        player=SimpleNamespace(
            player_id=player_id,
            ktc_value=ktc,
        ),
        custom_values=SimpleNamespace(
            dynasty_roster_war=personal_war,
            redraft_roster_war=None,
        ),
    )


def _personal_war(item):
    return item.custom_values.dynasty_roster_war


def test_match_package_rejects_underpay():
    sell_pool = [_item("a", 800.0, 1.0)]

    package = _match_package(
        sell_pool,
        target_ktc=2000.0,
    )

    assert package is None


def test_match_package_prefers_smallest_convincing_ratio():
    sell_pool = [
        _item("overpay", 2600.0, 1.0),
        _item("even", 2100.0, 1.0),
    ]

    package = _match_package(
        sell_pool,
        target_ktc=2000.0,
    )

    assert [i.player.player_id for i in package] == ["even"]


def test_match_package_pair_fallback_within_band():
    sell_pool = [
        _item("a", 1200.0, 1.0),
        _item("b", 1100.0, 1.0),
    ]

    package = _match_package(
        sell_pool,
        target_ktc=1500.0,
    )

    assert package is not None
    ratio = sum(i.player.ktc_value for i in package) / 1500.0
    assert COUNTERPARTY_KTC_MIN_RATIO <= ratio
    assert ratio <= COUNTERPARTY_KTC_MAX_RATIO


def test_match_package_respects_used_ids():
    used = {"even"}
    sell_pool = [
        _item("even", 2100.0, 1.0),
        _item("other", 2400.0, 1.0),
    ]

    package = _match_package(
        sell_pool,
        target_ktc=2000.0,
        used_player_ids=used,
    )

    assert [i.player.player_id for i in package] == ["other"]


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
