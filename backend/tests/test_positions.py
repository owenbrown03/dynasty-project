from app.domain.positions import (
    CORE_FANTASY_POSITION_SET,
    CORE_FANTASY_POSITIONS,
    POSITION_SORT_ORDER,
    is_core_fantasy_position,
)


def test_core_fantasy_positions_keep_shared_order():
    assert CORE_FANTASY_POSITIONS == (
        "QB",
        "RB",
        "WR",
        "TE",
    )
    assert CORE_FANTASY_POSITION_SET == {
        "QB",
        "RB",
        "WR",
        "TE",
    }


def test_position_sort_order_keeps_kicker_and_defense_after_core_positions():
    assert POSITION_SORT_ORDER["QB"] == 0
    assert POSITION_SORT_ORDER["TE"] == 3
    assert POSITION_SORT_ORDER["K"] == 4
    assert POSITION_SORT_ORDER["DEF"] == 5


def test_is_core_fantasy_position_rejects_non_core_positions():
    assert is_core_fantasy_position("RB") is True
    assert is_core_fantasy_position("K") is False
    assert is_core_fantasy_position(None) is False
