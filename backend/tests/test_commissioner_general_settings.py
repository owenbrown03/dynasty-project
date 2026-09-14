from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.schemas.commissioner import CommissionerSettingsUpdateRequest
from app.services.commissioner.general_settings import (
    get_commissioner_settings_overview,
    update_commissioner_settings,
)


@pytest.mark.anyio
async def test_get_commissioner_settings_overview(monkeypatch):
    mock_db = AsyncMock()
    ctx = SimpleNamespace(
        db=mock_db,
        redis=None,
        session=SimpleNamespace(),
        site_user=SimpleNamespace(id="site_user_id"),
        connection=SimpleNamespace(sleeper_user_id="sleeper_123"),
    )

    league = SimpleNamespace(
        league_id="l1",
        name="Best Ball Commish League",
        avatar=None,
        total_rosters=12,
        settings={
            "best_ball": 1,
            "bench_lock": 0,
            "trade_deadline": 11,
            "disable_trades": 0,
            "offseason_adds": 1,
        },
    )
    commish_row = SimpleNamespace(
        league=league,
        roster=SimpleNamespace(is_owner=True),
    )
    non_commish_row = SimpleNamespace(
        league=SimpleNamespace(
            league_id="l2",
            name="Other League",
            avatar=None,
            total_rosters=10,
            settings={},
        ),
        roster=SimpleNamespace(is_owner=False),
    )

    monkeypatch.setattr(
        "app.services.commissioner.general_settings.get_visible_owned_league_rows_by_sleeper_user_id",
        AsyncMock(return_value=[commish_row, non_commish_row]),
    )

    overview = await get_commissioner_settings_overview(ctx)
    assert len(overview) == 1
    assert overview[0].league_id == "l1"
    assert overview[0].league_name == "Best Ball Commish League"
    assert overview[0].best_ball == 1
    assert overview[0].bench_lock == 0
    assert overview[0].trade_deadline == 11
    assert overview[0].offseason_adds == 1


@pytest.mark.anyio
async def test_get_commissioner_settings_overview_preserves_sleeper_order(monkeypatch):
    mock_db = AsyncMock()
    ctx = SimpleNamespace(
        db=mock_db,
        redis=None,
        session=SimpleNamespace(),
        site_user=SimpleNamespace(id="site_user_id"),
        connection=SimpleNamespace(sleeper_user_id="sleeper_123"),
    )

    league_z = SimpleNamespace(
        league_id="lz",
        name="Zebra League",
        avatar=None,
        total_rosters=12,
        settings={"best_ball": 1},
    )
    league_a = SimpleNamespace(
        league_id="la",
        name="Alpha League",
        avatar=None,
        total_rosters=12,
        settings={"best_ball": 0},
    )
    row_z = SimpleNamespace(league=league_z, roster=SimpleNamespace(is_owner=True))
    row_a = SimpleNamespace(league=league_a, roster=SimpleNamespace(is_owner=True))

    monkeypatch.setattr(
        "app.services.commissioner.general_settings.get_visible_owned_league_rows_by_sleeper_user_id",
        AsyncMock(return_value=[row_z, row_a]),
    )
    monkeypatch.setattr(
        "app.services.commissioner.general_settings.get_league_sort_orders",
        AsyncMock(return_value={"lz": 0, "la": 1}),
    )

    overview = await get_commissioner_settings_overview(ctx)
    assert len(overview) == 2
    # Zebra League must stay first because Sleeper display_order is 0 < 1
    assert overview[0].league_id == "lz"
    assert overview[1].league_id == "la"



@pytest.mark.anyio
async def test_update_commissioner_settings_calls_sleeper_write(monkeypatch):
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_sleeper_write = AsyncMock()
    mock_sleeper_write.update_league_settings = AsyncMock(return_value={"settings": {"bench_lock": 1}})

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
    )

    league = SimpleNamespace(
        league_id="l1",
        name="Best Ball Commish League",
        settings={"best_ball": 1, "bench_lock": 0, "trade_deadline": 11},
    )
    commish_row = SimpleNamespace(
        league=league,
        roster=SimpleNamespace(is_owner=True),
    )

    monkeypatch.setattr(
        "app.services.commissioner.general_settings.get_visible_owned_league_rows_by_sleeper_user_id",
        AsyncMock(return_value=[commish_row]),
    )

    req = CommissionerSettingsUpdateRequest(
        league_ids=["l1"],
        bench_lock=1,
    )

    res = await update_commissioner_settings(ctx, req)
    assert res.total_leagues == 1
    assert res.successful_leagues == 1
    assert res.results[0].success is True

    # Verify sleeper write was called with updated bench_lock while keeping trade_deadline
    mock_sleeper_write.update_league_settings.assert_awaited_once()
    called_args = mock_sleeper_write.update_league_settings.await_args
    assert called_args.kwargs["league_id"] == "l1"
    assert called_args.kwargs["settings_map"]["bench_lock"] == 1
    assert called_args.kwargs["settings_map"]["best_ball"] == 1
    assert called_args.kwargs["settings_map"]["trade_deadline"] == 11
