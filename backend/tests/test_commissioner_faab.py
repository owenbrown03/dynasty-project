from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.core.context import Context
from app.schemas.commissioner import CommissionerFaabResetRequest
from app.services.commissioner.faab import (
    get_commissioner_faab_overview,
    reset_commissioner_faab,
)


@pytest.mark.anyio
async def test_get_commissioner_faab_overview_empty(monkeypatch):
    mock_db = AsyncMock()
    ctx = SimpleNamespace(
        db=mock_db,
        redis=None,
        session=SimpleNamespace(),
        site_user=SimpleNamespace(id="site_user_id"),
        connection=SimpleNamespace(sleeper_user_id="sleeper_123"),
        sleeper_write=None,
        sleeper=None,
        underdog=None,
    )

    monkeypatch.setattr(
        "app.services.commissioner.faab.get_visible_owned_league_rows_by_sleeper_user_id",
        AsyncMock(return_value=[]),
    )

    res = await get_commissioner_faab_overview(ctx)
    assert res == []


@pytest.mark.anyio
async def test_reset_commissioner_faab_calls_sleeper_write(monkeypatch):
    mock_db = AsyncMock()
    mock_sleeper_write = AsyncMock()
    mock_sleeper_write.auth.is_authenticated = MagicMock(return_value=True)
    mock_sleeper_write.reset_roster_faab = AsyncMock()

    ctx = SimpleNamespace(
        db=mock_db,
        redis=None,
        session=SimpleNamespace(),
        site_user=SimpleNamespace(id="site_user_id"),
        connection=SimpleNamespace(sleeper_user_id="sleeper_123"),
        sleeper_write=mock_sleeper_write,
        sleeper=None,
        underdog=None,
    )

    roster = SimpleNamespace(
        roster_id=1,
        owner_id="owner_1",
        settings={"waiver_budget_used": 10},
    )
    league = SimpleNamespace(
        league_id="league_1",
        name="League 1",
        avatar=None,
        settings={"waiver_budget": 100},
    )
    owned_row = SimpleNamespace(league=league)

    monkeypatch.setattr(
        "app.services.commissioner.faab.get_visible_owned_league_rows_by_sleeper_user_id",
        AsyncMock(return_value=[owned_row]),
    )
    monkeypatch.setattr(
        "app.services.commissioner.faab.get_all_rosters_by_league",
        AsyncMock(return_value={"league_1": [roster]}),
    )

    req = CommissionerFaabResetRequest(
        league_ids=["league_1"],
        target_budget=100,
    )
    res = await reset_commissioner_faab(ctx, req)

    assert res.total_leagues == 1
    assert res.successful_leagues == 1
    assert res.results[0].success is True
    assert res.results[0].rosters_reset == 1

    mock_sleeper_write.reset_roster_faab.assert_called_once_with(
        league_id="league_1",
        roster_id=1,
        target_budget=0,
    )
