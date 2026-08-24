from types import SimpleNamespace

from app.services.advisor.candidates import (
    _build_war_waiver_ladder,
    _passes_value_constraints,
)
from app.services.trades.waiver import split_waiver_credits


def _item(player_id, war):
    return SimpleNamespace(
        player=SimpleNamespace(
            player_id=player_id,
            fc_value=100.0,
        ),
        custom_values=SimpleNamespace(
            dynasty_roster_war=war,
            redraft_roster_war=None,
        ),
    )


def test_war_ladder_ranks_by_personal_war_and_skips_nulls():
    items = [
        _item("a", 3.0),
        _item("b", None),
        _item("c", 1.5),
        _item("d", 2.0),
    ]

    ladder = _build_war_waiver_ladder(
        items=items,
        total_rosters=2,
        roster_slots=2,
    )

    # Cutline 4; first replacement is rank-4 WAR = lowest non-null
    # (1.5), second slot steps up 10 ranks -> clamps to best available.
    assert len(ladder) >= 1
    assert abs(ladder[0] - 1.5) < 1e-9

    my_credit, their_credit = split_waiver_credits(
        my_players_out=2,
        their_players_out=1,
        ladder=ladder,
    )

    assert my_credit is not None and my_credit > 0
    assert their_credit is None


def test_war_ladder_empty_when_all_null():
    assert (
        _build_war_waiver_ladder(
            items=[_item("x", None)],
            total_rosters=12,
            roster_slots=20,
        )
        == []
    )


def test_constraints_count_war_credit_on_personal_side():
    # Without the war credit we lose personally; with it we tie.
    base = dict(
        market_send_total=110.0,
        market_receive_total=110.0,
        personal_send_total=2.0,
        personal_receive_total=1.8,
    )

    assert _passes_value_constraints(**base) is False
    assert (
        _passes_value_constraints(
            **base,
            my_waiver_credit_war=0.2,
        )
        is True
    )
