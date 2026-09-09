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
    mock_db.add = MagicMock()
    mock_sleeper_write = AsyncMock()
    mock_sleeper_write.reset_roster_faab = AsyncMock()

    mock_sleeper = MagicMock()
    mock_sleeper.can_write = True
    mock_sleeper.write = mock_sleeper_write

    ctx = SimpleNamespace(
        db=mock_db,
        redis=None,
        session=SimpleNamespace(),
        site_user=SimpleNamespace(id="site_user_id"),
        connection=SimpleNamespace(sleeper_user_id="sleeper_123"),
        sleeper=mock_sleeper,
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


@pytest.mark.anyio
async def test_reset_commissioner_faab_with_live_rosters(monkeypatch):
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_sleeper_write = AsyncMock()
    mock_sleeper_write.reset_roster_faab = AsyncMock()

    mock_sleeper_read = AsyncMock()
    mock_sleeper_read.get_rosters = AsyncMock(
        return_value=[
            {"roster_id": 1, "settings": {"waiver_budget_used": 25}},
            {"roster_id": 2, "settings": {"waiver_budget_used": 0}},
        ]
    )

    mock_sleeper = MagicMock()
    mock_sleeper.can_write = True
    mock_sleeper.write = mock_sleeper_write
    mock_sleeper.read = mock_sleeper_read

    ctx = SimpleNamespace(
        db=mock_db,
        redis=None,
        session=SimpleNamespace(),
        site_user=SimpleNamespace(id="site_user_id"),
        connection=SimpleNamespace(sleeper_user_id="sleeper_123"),
        sleeper=mock_sleeper,
        underdog=None,
    )

    roster1 = SimpleNamespace(
        roster_id=1,
        owner_id="owner_1",
        settings={"waiver_budget_used": 0},  # Stale DB had 0, but live had 25
    )
    roster2 = SimpleNamespace(
        roster_id=2,
        owner_id="owner_2",
        settings={"waiver_budget_used": 0},  # Live is 0, already matches target
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
        AsyncMock(return_value={"league_1": [roster1, roster2]}),
    )

    req = CommissionerFaabResetRequest(
        league_ids=["league_1"],
        target_budget=100,
    )
    res = await reset_commissioner_faab(ctx, req)

    assert res.total_leagues == 1
    assert res.successful_leagues == 1
    assert res.results[0].success is True
    # Only roster 1 needed reset because live had 25 spent and roster 2 had 0 spent
    assert res.results[0].rosters_reset == 1

    mock_sleeper_write.reset_roster_faab.assert_called_once_with(
        league_id="league_1",
        roster_id=1,
        target_budget=0,
    )


@pytest.mark.anyio
async def test_sleeper_write_reset_roster_faab():
    from app.integrations.sleeper.write import SleeperWrite

    mock_transport = AsyncMock()
    mock_auth = MagicMock()
    mock_auth.is_authenticated.return_value = True

    writer = SleeperWrite(transport=mock_transport, auth=mock_auth)
    writer.league_mutation = AsyncMock(return_value={"roster_update_settings": {}})

    await writer.reset_roster_faab(
        league_id="12345",
        roster_id=1,
        target_budget=0,
    )

    writer.league_mutation.assert_called_once_with(
        "roster_update_settings",
        "12345",
        {
            "roster_id": 1,
            "k_settings": ["waiver_budget_used"],
            "v_settings": [0],
        },
    )
