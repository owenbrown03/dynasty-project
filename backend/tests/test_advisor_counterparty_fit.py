from types import SimpleNamespace

from app.services.advisor.candidates import _counterparty_rank
from app.services.advisor.strategy import (
    COMPETE,
    HOARD_PICKS,
    REBUILD,
    WIN_NOW,
    LeagueStrategy,
)


def _s(strategy: str, fringe: bool = False) -> LeagueStrategy:
    return LeagueStrategy(strategy=strategy, reason="", fringe=fringe)


def test_win_now_prefers_rebuilders_first():
    mine = _s(WIN_NOW)

    ranks = {
        s: _counterparty_rank(_s(s), mine)
        for s in [REBUILD, HOARD_PICKS, COMPETE, WIN_NOW]
    }

    assert ranks[REBUILD] < ranks[HOARD_PICKS]
    assert ranks[HOARD_PICKS] < ranks[COMPETE]
    assert ranks[COMPETE] < ranks[WIN_NOW]


def test_rebuild_prefers_contenders_first():
    mine = _s(REBUILD)

    contender_rank = _counterparty_rank(_s(WIN_NOW), mine)
    fellow_rebuilder_rank = _counterparty_rank(_s(REBUILD), mine)

    assert contender_rank < fellow_rebuilder_rank


def test_fringe_tiebreak_beats_same_band():
    mine = None

    fringe_rank = _counterparty_rank(_s(COMPETE, fringe=True), mine)
    plain_rank = _counterparty_rank(_s(COMPETE), mine)

    assert fringe_rank < plain_rank


def test_unknown_direction_neutral():
    assert _counterparty_rank(None, None) == (1, 1)


def _unused():
    return SimpleNamespace()
