from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.schemas.commissioner import (
    CommissionerWaiverUpdateRequest,
    CommissionerStandardWaiverPresetUpdate,
)
from app.services.commissioner.waivers import (
    to_base4_str,
    decode_waiver_schedule,
    sun_sat_to_days_int,
    get_commissioner_waivers_overview,
    update_commissioner_waivers,
    get_commissioner_standard_waiver_preset,
    save_commissioner_standard_waiver_preset,
    reset_commissioner_standard_waiver_preset,
)
from app.crud.auth.user import reconcile_session_commissioner_standard_waivers


def test_waiver_schedule_encoding_decoding():
    # 5461 is all 1s (Waivers)
    assert to_base4_str(5461) == "1111111"
    schedule = decode_waiver_schedule(5461)
    assert len(schedule) == 7
    assert all(d.setting == 1 for d in schedule)

    # 10922 is all 2s (Locked)
    assert to_base4_str(10922) == "2222222"
    schedule_locked = decode_waiver_schedule(10922)
    assert all(d.setting == 2 for d in schedule_locked)

    # sun_sat: [Sun=0, Mon=2, Tue=2, Wed=1, Thu=3, Fri=3, Sat=0]
    # Sleeper internal Mon..Sun: 2213300 -> 10736
    encoded = sun_sat_to_days_int([0, 2, 2, 1, 3, 3, 0])
    assert encoded == 10736
    decoded = decode_waiver_schedule(encoded)
    days_dict = {d.day: d.setting for d in decoded}
    assert days_dict["Sunday"] == 0
    assert days_dict["Monday"] == 2
    assert days_dict["Tuesday"] == 2
    assert days_dict["Wednesday"] == 1
    assert days_dict["Thursday"] == 3
    assert days_dict["Friday"] == 3
    assert days_dict["Saturday"] == 0


@pytest.mark.anyio
async def test_get_commissioner_waivers_overview(monkeypatch):
    mock_db = AsyncMock()
    ctx = SimpleNamespace(
        db=mock_db,
        redis=None,
        session=SimpleNamespace(),
        site_user=SimpleNamespace(id="site_user_id"),
        connection=SimpleNamespace(sleeper_user_id="sleeper_123"),
        sleeper=None,
    )

    league = SimpleNamespace(
        league_id="l1",
        name="Commish League",
        avatar=None,
        total_rosters=12,
        settings={
            "daily_waivers": 1,
            "daily_waivers_days": 5461,
            "daily_waivers_hour": 0,
            "waiver_day_of_week": 0,
            "waiver_clear_days": 0,
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
        "app.services.commissioner.waivers.get_visible_owned_league_rows_by_sleeper_user_id",
        AsyncMock(return_value=[commish_row, non_commish_row]),
    )

    overview = await get_commissioner_waivers_overview(ctx)
    assert len(overview) == 1
    assert overview[0].league_id == "l1"
    assert overview[0].league_name == "Commish League"
    assert overview[0].daily_waivers == 1
    assert overview[0].daily_waivers_days == 5461
    assert overview[0].waiver_day_of_week == 0
    assert overview[0].waiver_clear_days == 0


@pytest.mark.anyio
async def test_update_commissioner_waivers_calls_sleeper_write(monkeypatch):
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_sleeper_write = AsyncMock()
    mock_sleeper_write.update_league_settings = AsyncMock(return_value={"settings": {"daily_waivers": 1}})

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
        name="Commish League",
        settings={"daily_waivers": 0, "daily_waivers_days": 5461, "daily_waivers_hour": 0},
    )
    commish_row = SimpleNamespace(
        league=league,
        roster=SimpleNamespace(is_owner=True),
    )

    monkeypatch.setattr(
        "app.services.commissioner.waivers.get_visible_owned_league_rows_by_sleeper_user_id",
        AsyncMock(return_value=[commish_row]),
    )

    req = CommissionerWaiverUpdateRequest(
        league_ids=["l1"],
        daily_waivers=1,
        sunday_to_saturday_settings=[0, 2, 2, 1, 3, 3, 0],
        daily_waivers_hour=9,
        waiver_day_of_week=0,
    )

    res = await update_commissioner_waivers(ctx, req)
    assert res.total_leagues == 1
    assert res.successful_leagues == 1
    assert res.results[0].success is True

    # Verify sleeper write was called
    mock_sleeper_write.update_league_settings.assert_awaited_once()
    called_args = mock_sleeper_write.update_league_settings.await_args
    assert called_args.kwargs["league_id"] == "l1"
    assert called_args.kwargs["settings_map"]["daily_waivers"] == 1
    assert called_args.kwargs["settings_map"]["daily_waivers_days"] == 10736
    assert called_args.kwargs["settings_map"]["daily_waivers_hour"] == 9
    assert called_args.kwargs["settings_map"]["waiver_day_of_week"] == 0


@pytest.mark.anyio
async def test_standard_waiver_preset_flow():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    site_user = SimpleNamespace(id="u1", settings={})
    session = SimpleNamespace(id=1, settings={})

    ctx = SimpleNamespace(
        db=mock_db,
        site_user=site_user,
        session=session,
    )

    # 1. Initially default preset is returned
    preset = await get_commissioner_standard_waiver_preset(ctx)
    assert preset.is_custom is False
    assert preset.sunday_to_saturday_settings == [3, 0, 1, 1, 3, 3, 3]

    # 2. Save custom preset
    custom_update = CommissionerStandardWaiverPresetUpdate(
        sunday_to_saturday_settings=[0, 0, 1, 1, 3, 0, 0],
        daily_waivers_hour=8,
        daily_waivers=1,
    )
    saved = await save_commissioner_standard_waiver_preset(ctx, custom_update)
    assert saved.is_custom is True
    assert saved.sunday_to_saturday_settings == [0, 0, 1, 1, 3, 0, 0]
    assert saved.daily_waivers_hour == 8

    # Verify site_user and session settings were updated
    assert site_user.settings["commissioner_standard_waivers"]["sunday_to_saturday_settings"] == [0, 0, 1, 1, 3, 0, 0]
    assert session.settings["commissioner_standard_waivers"]["sunday_to_saturday_settings"] == [0, 0, 1, 1, 3, 0, 0]

    # 3. Get should now return the custom preset
    loaded = await get_commissioner_standard_waiver_preset(ctx)
    assert loaded.is_custom is True
    assert loaded.sunday_to_saturday_settings == [0, 0, 1, 1, 3, 0, 0]
    assert loaded.daily_waivers_hour == 8

    # 4. Reset returns to default and removes custom
    reset_preset = await reset_commissioner_standard_waiver_preset(ctx)
    assert reset_preset.is_custom is False
    assert reset_preset.sunday_to_saturday_settings == [3, 0, 1, 1, 3, 3, 3]
    assert "commissioner_standard_waivers" not in site_user.settings
    assert "commissioner_standard_waivers" not in session.settings

    # 5. Test off-season preset
    offseason_default = await get_commissioner_standard_waiver_preset(ctx, preset_type="offseason")
    assert offseason_default.is_custom is False
    assert offseason_default.sunday_to_saturday_settings == [2, 2, 2, 1, 2, 2, 2]

    offseason_update = CommissionerStandardWaiverPresetUpdate(
        sunday_to_saturday_settings=[2, 2, 2, 2, 2, 2, 2],
        daily_waivers_hour=0,
        daily_waivers=1,
    )
    saved_offseason = await save_commissioner_standard_waiver_preset(
        ctx, offseason_update, preset_type="offseason"
    )
    assert saved_offseason.is_custom is True
    assert saved_offseason.sunday_to_saturday_settings == [2, 2, 2, 2, 2, 2, 2]
    assert site_user.settings["commissioner_offseason_waivers"]["sunday_to_saturday_settings"] == [2, 2, 2, 2, 2, 2, 2]

    loaded_offseason = await get_commissioner_standard_waiver_preset(ctx, preset_type="offseason")
    assert loaded_offseason.is_custom is True
    assert loaded_offseason.sunday_to_saturday_settings == [2, 2, 2, 2, 2, 2, 2]

    reset_offseason = await reset_commissioner_standard_waiver_preset(ctx, preset_type="offseason")
    assert reset_offseason.is_custom is False
    assert reset_offseason.sunday_to_saturday_settings == [2, 2, 2, 1, 2, 2, 2]
    assert "commissioner_offseason_waivers" not in site_user.settings


@pytest.mark.anyio
async def test_reconcile_session_commissioner_standard_waivers():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    user = SimpleNamespace(id="u1", settings={})
    session = SimpleNamespace(
        id=1,
        settings={
            "commissioner_standard_waivers": {
                "sunday_to_saturday_settings": [1, 1, 1, 1, 1, 1, 1],
                "daily_waivers_hour": 12,
                "daily_waivers": 1,
            },
            "commissioner_offseason_waivers": {
                "sunday_to_saturday_settings": [2, 2, 2, 1, 2, 2, 2],
                "daily_waivers_hour": 0,
                "daily_waivers": 1,
            },
        },
    )

    reconciled = await reconcile_session_commissioner_standard_waivers(
        user=user,
        session=session,
        db=mock_db,
    )
    assert "commissioner_standard_waivers" in reconciled.settings
    assert reconciled.settings["commissioner_standard_waivers"]["daily_waivers_hour"] == 12
    assert "commissioner_offseason_waivers" in reconciled.settings
    assert reconciled.settings["commissioner_offseason_waivers"]["daily_waivers_hour"] == 0

