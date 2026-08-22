from datetime import datetime, timedelta, timezone

from app.services.advisor.digest import is_report_stale


class _Report:
    def __init__(self, generated_at):
        self.generated_at = generated_at


def test_none_report_is_stale():
    assert is_report_stale(None) is True


def test_fresh_report_not_stale():
    report = _Report(datetime.now(timezone.utc))

    assert is_report_stale(report) is False


def test_old_report_is_stale():
    report = _Report(
        datetime.now(timezone.utc) - timedelta(days=8),
    )

    assert is_report_stale(report) is True


def test_naive_timestamp_treated_as_utc():
    naive = datetime.now(timezone.utc).replace(tzinfo=None)

    assert is_report_stale(_Report(naive)) is False
