import asyncio

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
