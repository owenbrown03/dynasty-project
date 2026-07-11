from datetime import datetime, timedelta

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
