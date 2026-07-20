import asyncio
from datetime import UTC, datetime

from app.crud import adp as adp_crud
from app.schemas.adp import ADPFilters
from app.services.adp.service import get_adp, invalidate_adp_cache


class FakeRedis:
    def __init__(self):
        self.store: dict[str, str] = {}
        self.deleted: list[str] = []
        self.deleted_prefixes: list[str] = []

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value: str, ttl_seconds: int):
        self.store[key] = value

    async def delete(self, key: str):
        self.deleted.append(key)
        self.store.pop(key, None)

    async def delete_prefix(self, prefix: str):
        self.deleted_prefixes.append(prefix)
        for key in list(self.store):
            if key.startswith(prefix):
                self.store.pop(key, None)


class FakeDB:
    pass


def test_get_adp_prefers_snapshot(monkeypatch):
    snapshot_generated_at = datetime.now(UTC)

    async def fake_get_latest_adp_snapshot(*args, **kwargs):
        return adp_crud.ADPSnapshotResult(
            snapshot_id="snapshot-1",
            sample=adp_crud.ADPSampleSummary(
                draft_count=12,
                pick_count=144,
                earliest_draft_at=datetime(2026, 1, 1, tzinfo=UTC),
                latest_draft_at=datetime(2026, 7, 1, tzinfo=UTC),
                generated_at=snapshot_generated_at,
                data_source="snapshot",
            ),
            players=[
                adp_crud.ADPPlayerAggregateRow(
                    player_id="1",
                    name="Test Player",
                    position="WR",
                    team="DAL",
                    overall_adp=10.5,
                    median_pick=10.0,
                    min_pick=3,
                    max_pick=18,
                    standard_deviation=4.2,
                    pick_count=20,
                    draft_count=12,
                    selection_rate=1.0,
                ),
            ],
        )

    async def fail_summary(*args, **kwargs):
        raise AssertionError("live summary should not run when snapshot exists")

    async def fail_aggregates(*args, **kwargs):
        raise AssertionError("live aggregates should not run when snapshot exists")

    monkeypatch.setattr(
        adp_crud,
        "get_latest_adp_snapshot",
        fake_get_latest_adp_snapshot,
    )
    monkeypatch.setattr(
        adp_crud,
        "get_adp_sample_summary",
        fail_summary,
    )
    monkeypatch.setattr(
        adp_crud,
        "get_player_adp_aggregates",
        fail_aggregates,
    )

    response = asyncio.run(
        get_adp(
            db=FakeDB(),
            redis=None,
            filters=ADPFilters(
                season="2026",
                draft_kind="startup",
                qb_format="superflex",
                minimum_draft_count=1,
                limit=10,
            ),
        )
    )

    assert response.sample.data_source == "snapshot"
    assert response.sample.generated_at == snapshot_generated_at
    assert response.players[0].name == "Test Player"


def test_get_adp_falls_back_to_live(monkeypatch):
    redis = FakeRedis()

    async def fake_get_latest_adp_snapshot(*args, **kwargs):
        return None

    async def fake_summary(*args, **kwargs):
        return adp_crud.ADPSampleSummary(
            draft_count=5,
            pick_count=60,
            earliest_draft_at=datetime(2026, 2, 1, tzinfo=UTC),
            latest_draft_at=datetime(2026, 3, 1, tzinfo=UTC),
        )

    async def fake_aggregates(*args, **kwargs):
        return [
            adp_crud.ADPPlayerAggregateRow(
                player_id="2",
                name="Live Player",
                position="QB",
                team="BUF",
                overall_adp=1.5,
                median_pick=1.0,
                min_pick=1,
                max_pick=4,
                standard_deviation=1.0,
                pick_count=5,
                draft_count=5,
                selection_rate=1.0,
            ),
        ]

    monkeypatch.setattr(
        adp_crud,
        "get_latest_adp_snapshot",
        fake_get_latest_adp_snapshot,
    )
    monkeypatch.setattr(
        adp_crud,
        "get_adp_sample_summary",
        fake_summary,
    )
    monkeypatch.setattr(
        adp_crud,
        "get_player_adp_aggregates",
        fake_aggregates,
    )

    response = asyncio.run(
        get_adp(
            db=FakeDB(),
            redis=redis,
            filters=ADPFilters(
                season="2026",
                draft_kind="startup",
                qb_format="superflex",
                minimum_draft_count=1,
                limit=10,
            ),
        )
    )

    assert response.sample.data_source == "live"
    assert response.players[0].name == "Live Player"
    assert redis.store


def test_get_adp_cache_ignores_limit(monkeypatch):
    redis = FakeRedis()
    aggregate_calls = 0

    async def fake_get_latest_adp_snapshot(*args, **kwargs):
        return None

    async def fake_summary(*args, **kwargs):
        return adp_crud.ADPSampleSummary(
            draft_count=5,
            pick_count=60,
            earliest_draft_at=datetime(2026, 2, 1, tzinfo=UTC),
            latest_draft_at=datetime(2026, 3, 1, tzinfo=UTC),
        )

    async def fake_aggregates(*args, **kwargs):
        nonlocal aggregate_calls
        aggregate_calls += 1
        return [
            adp_crud.ADPPlayerAggregateRow(
                player_id="2",
                name="Live Player",
                position="QB",
                team="BUF",
                overall_adp=1.5,
                median_pick=1.0,
                min_pick=1,
                max_pick=4,
                standard_deviation=1.0,
                pick_count=5,
                draft_count=5,
                selection_rate=1.0,
            ),
            adp_crud.ADPPlayerAggregateRow(
                player_id="3",
                name="Second Player",
                position="RB",
                team="ATL",
                overall_adp=2.5,
                median_pick=2.0,
                min_pick=2,
                max_pick=5,
                standard_deviation=1.0,
                pick_count=5,
                draft_count=5,
                selection_rate=1.0,
            ),
        ]

    monkeypatch.setattr(
        adp_crud,
        "get_latest_adp_snapshot",
        fake_get_latest_adp_snapshot,
    )
    monkeypatch.setattr(
        adp_crud,
        "get_adp_sample_summary",
        fake_summary,
    )
    monkeypatch.setattr(
        adp_crud,
        "get_player_adp_aggregates",
        fake_aggregates,
    )

    first_response = asyncio.run(
        get_adp(
            db=FakeDB(),
            redis=redis,
            filters=ADPFilters(
                season="2026",
                draft_kind="startup",
                qb_format="superflex",
                minimum_draft_count=1,
                limit=1,
            ),
        )
    )
    second_response = asyncio.run(
        get_adp(
            db=FakeDB(),
            redis=redis,
            filters=ADPFilters(
                season="2026",
                draft_kind="startup",
                qb_format="superflex",
                minimum_draft_count=1,
                limit=2,
            ),
        )
    )

    assert aggregate_calls == 1
    assert len(first_response.players) == 1
    assert len(second_response.players) == 2


def test_invalidate_adp_cache_clears_related_keys():
    redis = FakeRedis()
    filters = ADPFilters(
        season="2026",
        draft_kind="startup",
        qb_format="superflex",
        minimum_draft_count=1,
        limit=100,
    )

    asyncio.run(
        invalidate_adp_cache(
            redis,
            filters=filters,
        )
    )

    assert any(key.startswith("adp:v2:{") for key in redis.deleted)
    assert "adp:report" in redis.deleted
    assert "adp:metadata:" in redis.deleted_prefixes
