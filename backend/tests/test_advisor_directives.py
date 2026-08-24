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
    war=None,
) -> PersonalValuePoolItem:
    return PersonalValuePoolItem(
        player=PersonalValuePlayer(
            player_id=player_id,
            name=name,
            position="RB",
        ),
        market_values=PersonalValueMetrics(),
        custom_values=PersonalValueMetrics(
            dynasty_roster_war=war,
        ),
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


def test_drop_value_uses_personal_war():
    assert _drop_value(_item("1", "A", war=3.5)) == 3.5
    # Missing personal values sort as cut candidates, not errors.
    assert _drop_value(_item("2", "B", war=None)) == 0.0


def _ctx() -> SimpleNamespace:
    return SimpleNamespace(
        db=object(),
        connection=SimpleNamespace(sleeper_user_id="su-1"),
        site_user=None,
    )


def test_standard_league_excludes_parked_players_from_drops(monkeypatch):
    low = _item("p-low", "Low Value Guy", war=0.5)
    stash = _item("p-stash", "IR Stash Guy", war=9.0)

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
                players=["p-low", "p-unknown", "p-stash"],
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
    low = _item("p-low", "Low Value Guy", war=0.5)
    mid = _item("p-mid", "Mid Guy", war=2.0)
    high = _item("p-high", "High Guy", war=12.0)

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
