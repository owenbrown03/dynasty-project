from app.services.trades.waiver import (
    build_waiver_credit_ladder,
    split_waiver_credits,
    waiver_credit_for,
)


def _ladder():
    # 10 rostered players in a 2-team league; values descend.
    ranked = [5000 - i * 100 for i in range(50)]
    return build_waiver_credit_ladder(
        ranked,
        num_teams=2,
        roster_slots=5,
    )


def test_ladder_first_slot_is_cutline_player():
    ladder = _ladder()

    # cutline = 2*5 + 2 = 12 -> value 5000 - 1200 = 3800
    assert ladder[0] == 3800.0


def test_ladder_increases_per_extra_slot():
    ladder = _ladder()

    assert len(ladder) >= 2
    assert ladder[1] > ladder[0]
    assert ladder[1] == ladder[0] + (5000 - (12 - 10) * 100)


def test_even_trade_gets_no_credit():
    mine, theirs = split_waiver_credits(
        my_players_out=2,
        their_players_out=2,
        ladder=_ladder(),
    )

    assert mine is None
    assert theirs is None


def test_two_for_one_credits_side_shipping_more():
    mine, theirs = split_waiver_credits(
        my_players_out=2,
        their_players_out=1,
        ladder=_ladder(),
    )

    assert mine == _ladder()[0]
    assert theirs is None


def test_three_for_one_sums_two_slots():
    ladder = _ladder()
    mine, theirs = split_waiver_credits(
        my_players_out=3,
        their_players_out=1,
        ladder=ladder,
    )

    assert mine == ladder[1]


def test_zero_credit_ladder_returns_none():
    assert (
        waiver_credit_for(
            players_sent=3,
            players_received=1,
            ladder=[],
        )
        is None
    )
