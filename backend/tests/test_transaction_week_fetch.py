import pytest

from app.crud.sleeper.league import get_transaction_weeks_to_fetch


class TestGetTransactionWeeksToFetch:
    """Tests for the transaction week fetch window calculation."""

    def test_first_sync(self):
        """No prior sync — should fetch week 1."""
        assert get_transaction_weeks_to_fetch(
            last_synced_week=0, curr_week=1,
        ) == [1]

    def test_first_sync_week_zero(self):
        """Offseason with no prior sync."""
        assert get_transaction_weeks_to_fetch(
            last_synced_week=0, curr_week=0,
        ) == [0]

    def test_always_refetches_current_week(self):
        """Even when already synced through curr_week, re-fetch it."""
        assert get_transaction_weeks_to_fetch(
            last_synced_week=2, curr_week=2,
        ) == [1, 2]

    def test_always_refetches_previous_week(self):
        """Previous week is included to catch late-arriving transactions."""
        assert get_transaction_weeks_to_fetch(
            last_synced_week=5, curr_week=6,
        ) == [5, 6]

    def test_backfills_missing_weeks(self):
        """Gap between last synced and current is filled."""
        assert get_transaction_weeks_to_fetch(
            last_synced_week=3, curr_week=7,
        ) == [4, 5, 6, 7]

    def test_backfills_and_refetches_previous(self):
        """Gap + previous week when previous is outside the gap."""
        assert get_transaction_weeks_to_fetch(
            last_synced_week=5, curr_week=10,
        ) == [6, 7, 8, 9, 10]

    def test_no_duplicates(self):
        """Previous week already in range is not duplicated."""
        result = get_transaction_weeks_to_fetch(
            last_synced_week=0, curr_week=2,
        )
        assert result == sorted(set(result))

    def test_curr_week_one(self):
        """Previous week is 0 — should not be included (week 0 excluded by prev_week >= 1)."""
        assert get_transaction_weeks_to_fetch(
            last_synced_week=0, curr_week=1,
        ) == [1]

    def test_already_ahead(self):
        """last_synced_week > curr_week (shouldn't happen, but be safe)."""
        result = get_transaction_weeks_to_fetch(
            last_synced_week=5, curr_week=3,
        )
        # Should still fetch curr_week and prev
        assert 3 in result
        assert 2 in result
        assert result == sorted(result)

    def test_single_week_gap(self):
        """One week behind — fills gap and adds prev."""
        assert get_transaction_weeks_to_fetch(
            last_synced_week=7, curr_week=9,
        ) == [8, 9]
