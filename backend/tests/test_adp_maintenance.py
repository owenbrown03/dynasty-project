import asyncio
from types import SimpleNamespace

from app.services.adp import maintenance as maintenance_service


class FakeDB:
    pass


class FakeSleeperClient:
    pass


def test_run_adp_maintenance_aggregates_cycles(monkeypatch):
    seeded_calls: list[tuple[str, int | None]] = []
    processed_calls: list[tuple[int | None, bool]] = []
    ingested_calls: list[int] = []

    async def fake_seed_users(db, *, limit=None):
        seeded_calls.append(("users", limit))
        return 12

    discovery_results = [
        maintenance_service.ADPDiscoveryBatchResult(
            claimed_node_count=50,
            processed_node_count=40,
            discovered_user_count=0,
            discovered_league_count=0,
            discovered_draft_count=25,
            request_count=50,
            stopped_reason=None,
        ),
        maintenance_service.ADPDiscoveryBatchResult(
            claimed_node_count=50,
            processed_node_count=35,
            discovered_user_count=0,
            discovered_league_count=0,
            discovered_draft_count=15,
            request_count=45,
            stopped_reason=None,
        ),
    ]

    async def fake_process(
        db,
        sleeper,
        *,
        max_nodes=None,
        allow_when_disabled=False,
        discover_users=True,
    ):
        processed_calls.append((max_nodes, discover_users))
        return discovery_results[len(processed_calls) - 1]

    ingested_results = [
        [
            SimpleNamespace(is_qualified=True),
            SimpleNamespace(is_qualified=False),
        ],
        [
            SimpleNamespace(is_qualified=True),
        ],
    ]

    async def fake_ingest(db, sleeper, *, max_drafts):
        ingested_calls.append(max_drafts)
        return ingested_results[len(ingested_calls) - 1]

    monkeypatch.setattr(
        maintenance_service,
        "seed_existing_users_for_adp_discovery",
        fake_seed_users,
    )
    monkeypatch.setattr(
        maintenance_service,
        "process_adp_discovery_batch",
        fake_process,
    )
    monkeypatch.setattr(
        maintenance_service,
        "ingest_discovered_drafts",
        fake_ingest,
    )

    result = asyncio.run(
        maintenance_service.run_adp_maintenance(
            FakeDB(),
            FakeSleeperClient(),
            seed_source="users",
            seed_limit=250,
            cycles=2,
            max_nodes_per_cycle=50,
            max_drafts_per_cycle=200,
            allow_when_disabled=True,
            discover_users=False,
        )
    )

    assert seeded_calls == [("users", 250)]
    assert processed_calls == [(50, False), (50, False)]
    assert ingested_calls == [200, 200]
    assert result.seeded_count == 12
    assert result.completed_cycles == 2
    assert result.total_processed_nodes == 75
    assert result.total_discovered_drafts == 40
    assert result.total_requests == 95
    assert result.total_ingested_drafts == 3
    assert result.total_qualified_drafts == 2
