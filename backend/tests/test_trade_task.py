import asyncio
import pytest

from app.tasks import trade as trade_task


class FakeRedis:
    def __init__(self):
        self.values: dict[str, str] = {}

    async def set(
        self,
        key: str,
        value: str,
        ex: int | None = None,
        nx: bool = False,
    ):
        del ex

        if nx and key in self.values:
            return False

        self.values[key] = value
        return True

    async def get(
        self,
        key: str,
    ):
        return self.values.get(
            key,
        )

    async def delete(
        self,
        key: str,
    ):
        self.values.pop(
            key,
            None,
        )


class FakeSession:
    async def __aenter__(self):
        return self

    async def __aexit__(
        self,
        exc_type,
        exc,
        tb,
    ):
        return False

    async def commit(self):
        return None


def test_sync_leaguemates_task_skips_when_lock_exists(
    monkeypatch,
):
    fake_redis = FakeRedis()
    fake_redis.values[
        trade_task._leaguemate_sync_lock_key(
            "browntown333",
        )
    ] = "existing"

    async def fake_get_redis():
        return fake_redis

    async def fail_sync(*args, **kwargs):
        raise AssertionError(
            "sync should not run while locked",
        )

    monkeypatch.setattr(
        trade_task.RedisManager,
        "get",
        fake_get_redis,
    )
    monkeypatch.setattr(
        trade_task,
        "AsyncSessionLocal",
        lambda: FakeSession(),
    )
    monkeypatch.setattr(
        trade_task,
        "sync_leaguemates",
        fail_sync,
    )

    result = asyncio.run(
        trade_task.sync_leaguemates_task(
            "browntown333",
        )
    )

    assert result == {
        "status": "skipped",
        "reason": "already_running",
        "username": "browntown333",
    }


def test_sync_leaguemates_task_releases_lock_after_success(
    monkeypatch,
):
    fake_redis = FakeRedis()
    sync_calls: list[str] = []

    async def fake_get_redis():
        return fake_redis

    async def fake_get_worker_sleeper_client():
        return object()

    async def fake_sync_leaguemates(
        db,
        sleeper,
        username,
        force=False,
    ):
        del db, sleeper
        sync_calls.append(
            username,
        )
        return {
            "status": "completed",
            "username": username,
        }

    monkeypatch.setattr(
        trade_task.RedisManager,
        "get",
        fake_get_redis,
    )
    monkeypatch.setattr(
        trade_task,
        "AsyncSessionLocal",
        lambda: FakeSession(),
    )
    monkeypatch.setattr(
        trade_task,
        "get_worker_sleeper_client",
        fake_get_worker_sleeper_client,
    )
    monkeypatch.setattr(
        trade_task,
        "sync_leaguemates",
        fake_sync_leaguemates,
    )

    result = asyncio.run(
        trade_task.sync_leaguemates_task(
            "browntown333",
        )
    )

    assert result == {
        "status": "completed",
        "username": "browntown333",
    }
    assert sync_calls == [
        "browntown333",
    ]
    assert fake_redis.values == {}


def test_is_in_leaguemate_sync_window():
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from app.tasks.trade import is_in_leaguemate_sync_window

    tz = ZoneInfo("America/Denver")
    in_win, dt1 = is_in_leaguemate_sync_window(
        now=datetime(2026, 11, 19, 3, 30, tzinfo=tz),
    )
    assert in_win is True

    out_win_day, dt2 = is_in_leaguemate_sync_window(
        now=datetime(2026, 11, 19, 10, 30, tzinfo=tz),
    )
    assert out_win_day is False

    out_win_early, dt3 = is_in_leaguemate_sync_window(
        now=datetime(2026, 11, 19, 2, 59, tzinfo=tz),
    )
    assert out_win_early is False

    out_win_late, dt4 = is_in_leaguemate_sync_window(
        now=datetime(2026, 11, 19, 5, 0, tzinfo=tz),
    )
    assert out_win_late is False


def test_run_daily_leaguemate_syncs_task_skips_outside_window(monkeypatch):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    tz = ZoneInfo("America/Denver")
    now_day = datetime(2026, 11, 19, 10, 30, tzinfo=tz)

    result = asyncio.run(
        trade_task.run_daily_leaguemate_syncs_task(
            force=False,
            now=now_day,
        )
    )

    assert result["status"] == "skipped"
    assert result["reason"] == "outside_scheduled_window"


def test_run_daily_leaguemate_syncs_task_enqueues_account_linked_users(monkeypatch):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from unittest.mock import AsyncMock

    fake_redis = FakeRedis()
    enqueued_users: list[str] = []

    async def fake_get_redis():
        return fake_redis

    async def fake_get_active_sleeper_usernames(db, accounts_only=False):
        assert accounts_only is True
        return ["browntown333"]

    monkeypatch.setattr(trade_task.RedisManager, "get", fake_get_redis)
    monkeypatch.setattr(trade_task, "AsyncSessionLocal", lambda: FakeSession())

    # mock get_active_sleeper_usernames
    import app.crud.sleeper.user as user_crud
    monkeypatch.setattr(user_crud, "get_active_sleeper_usernames", fake_get_active_sleeper_usernames)

    mock_kiq = AsyncMock()
    monkeypatch.setattr(trade_task.sync_leaguemates_task, "kiq", mock_kiq)

    tz = ZoneInfo("America/Denver")
    now_overnight = datetime(2026, 11, 19, 3, 30, tzinfo=tz)

    result = asyncio.run(
        trade_task.run_daily_leaguemate_syncs_task(
            force=False,
            now=now_overnight,
        )
    )

    assert result["status"] == "enqueued"
    assert result["usernames"] == ["browntown333"]
    assert result["date"] == "2026-11-19"
    mock_kiq.assert_awaited_once_with("browntown333", force=True)

    # Verify Redis keys were set
    assert fake_redis.values.get("leaguemates:daily_sync:last_run:2026-11-19") == "1"
    assert fake_redis.values.get("leaguemates:daily_sync:last_run") == "1"


def test_run_daily_leaguemate_syncs_task_skips_when_already_ran_today(monkeypatch):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    fake_redis = FakeRedis()
    fake_redis.values["leaguemates:daily_sync:last_run:2026-11-19"] = "1"

    async def fake_get_redis():
        return fake_redis

    monkeypatch.setattr(trade_task.RedisManager, "get", fake_get_redis)

    tz = ZoneInfo("America/Denver")
    now_overnight = datetime(2026, 11, 19, 4, 15, tzinfo=tz)

    result = asyncio.run(
        trade_task.run_daily_leaguemate_syncs_task(
            force=False,
            now=now_overnight,
        )
    )

    assert result["status"] == "skipped"
    assert result["reason"] == "already_ran_today"
    assert result["date"] == "2026-11-19"


def test_run_daily_leaguemate_syncs_task_force_overrides_window_and_ran_state(monkeypatch):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from unittest.mock import AsyncMock

    fake_redis = FakeRedis()
    fake_redis.values["leaguemates:daily_sync:last_run:2026-11-19"] = "1"

    async def fake_get_redis():
        return fake_redis

    async def fake_get_active_sleeper_usernames(db, accounts_only=False):
        return ["browntown333"]

    monkeypatch.setattr(trade_task.RedisManager, "get", fake_get_redis)
    monkeypatch.setattr(trade_task, "AsyncSessionLocal", lambda: FakeSession())

    import app.crud.sleeper.user as user_crud
    monkeypatch.setattr(user_crud, "get_active_sleeper_usernames", fake_get_active_sleeper_usernames)

    mock_kiq = AsyncMock()
    monkeypatch.setattr(trade_task.sync_leaguemates_task, "kiq", mock_kiq)

    tz = ZoneInfo("America/Denver")
    now_midday = datetime(2026, 11, 19, 14, 0, tzinfo=tz)

    result = asyncio.run(
        trade_task.run_daily_leaguemate_syncs_task(
            force=True,
            now=now_midday,
        )
    )

    assert result["status"] == "enqueued"
    assert result["usernames"] == ["browntown333"]
    mock_kiq.assert_awaited_once_with("browntown333", force=True)


@pytest.mark.anyio
async def test_get_active_sleeper_usernames_accounts_only_statement_structure():
    from app.crud.sleeper.user import get_active_sleeper_usernames
    from unittest.mock import AsyncMock, MagicMock

    db = AsyncMock()
    mock_res1 = MagicMock()
    mock_res1.scalars.return_value = ["user1"]
    mock_res2 = MagicMock()
    mock_res2.scalars.return_value = ["user2"]
    db.execute.side_effect = [mock_res1, mock_res2]

    users = await get_active_sleeper_usernames(db, accounts_only=True)
    assert users == ["user1", "user2"]

    call_args_list = db.execute.call_args_list
    assert len(call_args_list) == 2
    stmt1 = str(call_args_list[0][0][0])
    stmt2 = str(call_args_list[1][0][0])
    assert "site_user_id IS NOT NULL" in stmt1
    assert "site_user_id IS NOT NULL" in stmt2


