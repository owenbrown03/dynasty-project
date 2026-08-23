from app.services.trades.waiver import (
    build_waiver_credit_ladder,
    split_waiver_credits,
    waiver_credit_for,
)


def _ladder():
    # 400 ranked players keyed by FC's own overall_rank; the
    # cutline anchors at rank 300 (FC's average 11.3t x 26.7s league).
    values_by_rank = {
        rank + 1: 6000 - rank * 10 for rank in range(400)
    }
    return build_waiver_credit_ladder(
        values_by_rank=values_by_rank,
        cutline=300,
    )


def test_ladder_first_slot_is_cutline_player():
    ladder = _ladder()

    # anchor rank 300 -> value 6000 - 2990 = 3010
    assert ladder[0] == 3010.0


def test_ladder_increases_per_extra_slot():
    ladder = _ladder()

    assert len(ladder) >= 2
    assert ladder[1] > ladder[0]
    # second slot steps 10 ranks up: rank 290 -> 6000 - 2890 = 3110
    assert ladder[1] == ladder[0] + 3110.0


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
