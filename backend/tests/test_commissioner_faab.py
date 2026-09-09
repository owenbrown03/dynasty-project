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
        existing_settings={"waiver_budget_used": 10},
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
            {
                "roster_id": 1,
                "settings": {"waiver_budget_used": 25, "waiver_position": 4, "wins": 3},
            },
            {
                "roster_id": 2,
                "settings": {"waiver_budget_used": 0, "waiver_position": 2, "wins": 5},
            },
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
        settings={"waiver_budget_used": 0, "waiver_position": 4},
    )
    roster2 = SimpleNamespace(
        roster_id=2,
        owner_id="owner_2",
        settings={"waiver_budget_used": 0, "waiver_position": 2},
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
    assert res.results[0].rosters_reset == 1

    mock_sleeper_write.reset_roster_faab.assert_called_once_with(
        league_id="league_1",
        roster_id=1,
        target_budget=0,
        existing_settings={"waiver_budget_used": 25, "waiver_position": 4, "wins": 3},
    )


@pytest.mark.anyio
async def test_sleeper_write_reset_roster_faab_preserves_settings():
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
        existing_settings={
            "fpts": 100,
            "wins": 5,
            "losses": 2,
            "waiver_position": 7,
            "waiver_budget_used": 35,
        },
    )

    writer.league_mutation.assert_called_once()
    call_args = writer.league_mutation.call_args[0]
    assert call_args[0] == "roster_update_settings"
    assert call_args[1] == "12345"
    vars_passed = call_args[2]
    assert vars_passed["roster_id"] == 1
    settings_dict = dict(zip(vars_passed["k_settings"], vars_passed["v_settings"]))
    assert settings_dict["waiver_position"] == 7
    assert settings_dict["waiver_budget_used"] == 0
    assert settings_dict["wins"] == 5
    assert settings_dict["losses"] == 2


@pytest.mark.anyio
async def test_reset_commissioner_faab_custom_amount_with_live_league_budget(monkeypatch):
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_sleeper_write = AsyncMock()
    mock_sleeper_write.reset_roster_faab = AsyncMock()

    # Live league has budget 67 (local DB had stale 100)
    mock_sleeper_read = AsyncMock()
    mock_sleeper_read.get_league = AsyncMock(
        return_value=SimpleNamespace(
            settings=SimpleNamespace(
                model_dump=lambda: {"waiver_budget": 67}
            )
        )
    )
    mock_sleeper_read.get_rosters = AsyncMock(
        return_value=[
            SimpleNamespace(
                roster_id=1,
                settings=SimpleNamespace(
                    model_dump=lambda: {"waiver_budget_used": 0, "waiver_position": 12}
                ),
            )
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

    roster = SimpleNamespace(
        roster_id=1,
        owner_id="owner_1",
        settings={"waiver_budget_used": 0, "waiver_position": 12},
    )
    league = SimpleNamespace(
        league_id="league_1",
        name="League 1",
        avatar=None,
        settings={"waiver_budget": 100},  # Stale DB had 100
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

    # User requests custom reset to $23
    req = CommissionerFaabResetRequest(
        league_ids=["league_1"],
        target_budget=23,
    )
    res = await reset_commissioner_faab(ctx, req)

    assert res.total_leagues == 1
    assert res.successful_leagues == 1
    assert res.results[0].success is True
    assert res.results[0].rosters_reset == 1

    # Live budget = 67, target = 23 -> target_used must be 67 - 23 = 44
    mock_sleeper_write.reset_roster_faab.assert_called_once_with(
        league_id="league_1",
        roster_id=1,
        target_budget=44,
        existing_settings={"waiver_budget_used": 0, "waiver_position": 12},
    )
