import asyncio
from types import SimpleNamespace

from app.models.db.sleeper.api import League, Roster
from app.schemas.personal_values import (
    PersonalValueMetrics,
    PersonalValuePlayer,
    PersonalValuePoolGroup,
    PersonalValuePoolItem,
)
from app.services.advisor import directives as directives_service
from app.services.advisor.directives import (
    _drop_value,
    build_advisor_directives,
)


def _item(
    player_id: str,
    name: str,
    ktc=None,
    fc=None,
) -> PersonalValuePoolItem:
    return PersonalValuePoolItem(
        player=PersonalValuePlayer(
            player_id=player_id,
            name=name,
            position="RB",
            ktc_value=ktc,
            fc_value=fc,
        ),
        market_values=PersonalValueMetrics(),
        custom_values=PersonalValueMetrics(),
        delta_values=PersonalValueMetrics(),
    )


def _pool(items) -> SimpleNamespace:
    return SimpleNamespace(
        groups=[
            PersonalValuePoolGroup(
                position="RB",
                players=list(items),
            ),
        ],
    )


def _league(league_id: str, *, best_ball: bool, roster_size: int) -> League:
    return League(
        league_id=league_id,
        name=f"League {league_id}",
        season="2026",
        type="redraft" if not best_ball else "best_ball",
        total_rosters=12,
        draft_id=f"draft-{league_id}",
        settings={
            "best_ball": 1 if best_ball else 0,
            "reserve_slots": 1,
            "taxi_slots": 1,
        },
        # Effective size comes from non-IR/TAXI lineup slots.
        roster_positions=["QB", "RB"][:roster_size],
    )


def test_drop_value_fallback_chain():
    assert _drop_value(_item("1", "A", ktc=100, fc=90), "ktc") == 100
    assert _drop_value(_item("2", "B", ktc=None, fc=90), "ktc") == 90
    # Requesting fantasycalc falls back to ktc when fc missing.
    assert _drop_value(_item("3", "C", ktc=55, fc=None), "fantasycalc") == 55
    # Missing both values sorts as a cut candidate, not an error.
    assert _drop_value(_item("4", "D", ktc=None, fc=None), "ktc") == 0.0


def _ctx() -> SimpleNamespace:
    return SimpleNamespace(
        db=object(),
        connection=SimpleNamespace(sleeper_user_id="su-1"),
        site_user=None,
    )


def test_standard_league_excludes_parked_players_from_drops(monkeypatch):
    low = _item("p-low", "Low Value Guy", ktc=10)
    stash = _item("p-stash", "IR Stash Guy", ktc=200)

    # Standard league: capacity = effective roster size (2) +
    # occupied reserve (1) = 3. Three rostered players -> NOT over
    # limit even with a full reserve slot; parked players are
    # excluded from suggestions.
    rows = [
        SimpleNamespace(
            league=_league("standard-1", best_ball=False, roster_size=2),
            roster=Roster(
                roster_id=1,
                league_id="standard-1",
                players=["p-low", "p-mid-missing", "p-stash"],
                reserve=["p-stash"],
            ),
        ),
    ]

    async def fake_rows(**kwargs):
        return rows

    async def fake_pool(*, ctx, league_id):
        return _pool([low, stash])

    monkeypatch.setattr(
        directives_service,
        "get_visible_owned_league_rows_by_sleeper_user_id",
        fake_rows,
    )
    monkeypatch.setattr(
        directives_service,
        "get_personal_value_pool",
        fake_pool,
    )

    result = asyncio.run(build_advisor_directives(_ctx(), "testuser"))

    assert result.directives == []


def test_best_ball_counts_parked_players_and_over_limit_drops_lowest(
    monkeypatch,
):
    low = _item("p-low", "Low Value Guy", ktc=10)
    mid = _item("p-mid", "Mid Guy", ktc=50)
    high = _item("p-high", "High Guy", ktc=900)

    # Best ball: capacity == roster_size regardless of reserve. With
    # roster_size 2 and three rostered players -> over by 1; the
    # lowest-value active player is the suggested cut.
    rows = [
        SimpleNamespace(
            league=_league("bb-1", best_ball=True, roster_size=2),
            roster=Roster(
                roster_id=1,
                league_id="bb-1",
                players=["p-low", "p-mid", "p-high"],
                reserve=[],
            ),
        ),
    ]

    async def fake_rows(**kwargs):
        return rows

    async def fake_pool(*, ctx, league_id):
        return _pool([low, mid, high])

    monkeypatch.setattr(
        directives_service,
        "get_visible_owned_league_rows_by_sleeper_user_id",
        fake_rows,
    )
    monkeypatch.setattr(
        directives_service,
        "get_personal_value_pool",
        fake_pool,
    )

    result = asyncio.run(build_advisor_directives(_ctx(), "testuser"))

    assert len(result.directives) == 1
    directive = result.directives[0]
    assert directive.over_limit_by == 1
    assert directive.status == "pre_draft"
    assert [d.player_id for d in directive.suggested_drops] == ["p-low"]


def test_no_connection_yields_empty_directives():
    ctx = _ctx()
    ctx.connection = None

    result = asyncio.run(build_advisor_directives(ctx, "testuser"))
    assert result.directives == []
