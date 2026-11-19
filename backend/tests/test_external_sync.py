from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.services.sync.external import should_run_daily_external_sync


def test_daily_external_sync_runs_when_missing_timestamp():
    assert should_run_daily_external_sync(
        None,
    ) is True


def test_daily_external_sync_skips_when_recent():
    now = datetime(2026, 7, 11, 12, 0, 0)

    assert should_run_daily_external_sync(
        now - timedelta(hours=6),
        now=now,
    ) is False


def test_daily_external_sync_runs_when_stale():
    now = datetime(2026, 7, 11, 12, 0, 0)

    assert should_run_daily_external_sync(
        now - timedelta(days=1, minutes=1),
        now=now,
    ) is True


def test_daily_external_sync_force_overrides_freshness():
    now = datetime(2026, 7, 11, 12, 0, 0)

    assert should_run_daily_external_sync(
        now - timedelta(hours=1),
        now=now,
        force=True,
    ) is True


@pytest.mark.anyio
async def test_run_daily_external_syncs_resilient_to_underdog_error():
    from unittest.mock import AsyncMock, MagicMock, patch
    from app.services.sync.external import run_daily_external_syncs

    mock_db = AsyncMock()
    mock_db_cm = MagicMock()
    mock_db_cm.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db_cm.__aexit__ = AsyncMock(return_value=None)

    adp_res = MagicMock(
        seeded_count=5,
        completed_cycles=1,
        total_processed_nodes=2,
        total_discovered_drafts=3,
        total_ingested_drafts=3,
        total_qualified_drafts=3,
        stopped_reason="cycle_limit",
    )

    with (
        patch("app.services.sync.external.acquire_daily_external_sync_lock", AsyncMock(return_value="lock-123")),
        patch("app.services.sync.external.release_daily_external_sync_lock", AsyncMock()),
        patch("app.services.sync.external.AsyncSessionLocal", return_value=mock_db_cm),
        patch("app.services.sync.external.get_daily_external_sync_state", AsyncMock(return_value=None)),
        patch("app.services.sync.external.get_worker_sleeper_client", AsyncMock()),
        patch("app.services.sync.external.HTTPClientManager.get", AsyncMock()),
        patch("app.services.sync.external.sync_players", AsyncMock()),
        patch("app.services.sync.external.sync_projections", AsyncMock()),
        patch("app.services.sync.external.sync_recent_regular_season_stats", AsyncMock()),
        patch("app.services.sync.external.sync_ktc_values", AsyncMock(return_value={"matched": 100})),
        patch("app.services.sync.external.sync_fantasycalc_values", AsyncMock(return_value={"matched": 100})),
        patch("app.services.sync.external.sync_underdog_adp", AsyncMock(side_effect=RuntimeError("No active NFL best ball slates found."))),
        patch("app.services.sync.external.run_adp_maintenance", AsyncMock(return_value=adp_res)) as mock_adp,
        patch("app.services.sync.external.update_daily_external_sync_state", AsyncMock()) as mock_update_state,
    ):
        result = await run_daily_external_syncs(force=True)

        assert result["status"] == "complete"
        assert result["underdog"]["status"] == "error"
        assert "No active NFL best ball slates found." in result["underdog"]["reason"]
        mock_adp.assert_awaited_once()
        mock_update_state.assert_awaited_once()

