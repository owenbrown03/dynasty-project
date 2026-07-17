import asyncio
from types import SimpleNamespace

from app.crud import adp as adp_crud
from app.services.adp import discovery as discovery_service


class FakeSleeperRead:
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    async def get_drafts_league(self, league_id):
        self.calls.append(("get_drafts_league", league_id))
        return [
            SimpleNamespace(draft_id=f"{league_id}-draft-1"),
            SimpleNamespace(draft_id=f"{league_id}-draft-2"),
        ]

    async def get_users(self, league_id):
        self.calls.append(("get_users", league_id))
        return [
            SimpleNamespace(user_id=f"{league_id}-user-1"),
            SimpleNamespace(user_id=f"{league_id}-user-2"),
        ]

    async def get_leagues(self, user_id, season):
        self.calls.append(("get_leagues", f"{user_id}:{season}"))
        return [
            SimpleNamespace(league_id=f"{user_id}-{season}-league-1"),
            SimpleNamespace(league_id=f"{user_id}-{season}-league-2"),
        ]


class FakeSleeperClient:
    def __init__(self):
        self.read = FakeSleeperRead()


class FakeDB:
    async def commit(self):
        return None


def test_enqueue_discovery_nodes_dedupes_in_batch():
    rows = [
        {"node_type": "league_id", "node_value": "league-1"},
        {"node_type": "league_id", "node_value": "league-1"},
        {"node_type": "draft_id", "node_value": "draft-1"},
    ]

    deduped = adp_crud._dedupe_discovery_rows(rows)

    assert deduped == [
        {"node_type": "league_id", "node_value": "league-1"},
        {"node_type": "draft_id", "node_value": "draft-1"},
    ]


def test_process_discovery_batch_league_node_enqueues_users_and_drafts(
    monkeypatch,
):
    captured_rows: list[dict] = []
    processed_ids: list[str] = []

    async def fake_claim_discovery_nodes(*args, **kwargs):
        return [
            SimpleNamespace(
                id="node-1",
                node_type="league_id",
                node_value="league-1",
                discovery_depth=0,
            )
        ]

    async def fake_enqueue_discovery_nodes(db, rows):
        captured_rows.extend(rows)
        return len(rows)

    async def fake_mark_processed(db, *, node_id):
        processed_ids.append(node_id)

    async def fake_mark_failed(*args, **kwargs):
        return None

    async def fake_release_nodes(db, *, node_ids):
        raise AssertionError("should not release nodes")

    monkeypatch.setattr(
        adp_crud,
        "claim_discovery_nodes",
        fake_claim_discovery_nodes,
    )
    monkeypatch.setattr(
        adp_crud,
        "enqueue_discovery_nodes",
        fake_enqueue_discovery_nodes,
    )
    monkeypatch.setattr(
        adp_crud,
        "mark_discovery_node_processed",
        fake_mark_processed,
    )
    monkeypatch.setattr(
        adp_crud,
        "mark_discovery_node_failed",
        fake_mark_failed,
    )
    monkeypatch.setattr(
        adp_crud,
        "release_discovery_nodes",
        fake_release_nodes,
    )
    monkeypatch.setattr(discovery_service.settings, "ADP_CRAWL_ENABLED", True)
    monkeypatch.setattr(discovery_service.settings, "ADP_MAX_REQUESTS_PER_RUN", 10)
    monkeypatch.setattr(discovery_service.settings, "ADP_MAX_NEW_USERS_PER_RUN", 10)
    monkeypatch.setattr(discovery_service.settings, "ADP_MAX_NEW_DRAFTS_PER_RUN", 10)
    monkeypatch.setattr(discovery_service.settings, "ADP_MAX_NEW_LEAGUES_PER_RUN", 10)
    monkeypatch.setattr(discovery_service.settings, "ADP_MAX_DISCOVERY_DEPTH", 2)
    monkeypatch.setattr(discovery_service.settings, "ADP_MAX_NODES_PER_RUN", 10)
    monkeypatch.setattr(discovery_service.settings, "ADP_MAX_RUNTIME_SECONDS", 300)
    monkeypatch.setattr(discovery_service.settings, "ADP_PROCESSING_TIMEOUT_SECONDS", 900)

    result = asyncio.run(
        discovery_service.process_adp_discovery_batch(
            FakeDB(),
            FakeSleeperClient(),
        )
    )

    assert result.processed_node_count == 1
    assert result.discovered_draft_count == 2
    assert result.discovered_user_count == 2
    assert result.request_count == 2
    assert processed_ids == ["node-1"]
    assert {row["node_type"] for row in captured_rows} == {"draft_id", "user_id"}
    assert all(row["source_type"] == "league_id" for row in captured_rows)
    assert all(row["discovery_depth"] == 1 for row in captured_rows)


def test_process_discovery_batch_user_node_honors_league_budget(
    monkeypatch,
):
    captured_rows: list[dict] = []

    async def fake_claim_discovery_nodes(*args, **kwargs):
        return [
            SimpleNamespace(
                id="user-node-1",
                node_type="user_id",
                node_value="user-1",
                discovery_depth=0,
            )
        ]

    async def fake_enqueue_discovery_nodes(db, rows):
        captured_rows.extend(rows)
        return len(rows)

    async def fake_mark_processed(*args, **kwargs):
        return None

    async def fake_mark_failed(*args, **kwargs):
        return None

    async def fake_release_nodes(*args, **kwargs):
        return None

    monkeypatch.setattr(
        adp_crud,
        "claim_discovery_nodes",
        fake_claim_discovery_nodes,
    )
    monkeypatch.setattr(
        adp_crud,
        "enqueue_discovery_nodes",
        fake_enqueue_discovery_nodes,
    )
    monkeypatch.setattr(
        adp_crud,
        "mark_discovery_node_processed",
        fake_mark_processed,
    )
    monkeypatch.setattr(
        adp_crud,
        "mark_discovery_node_failed",
        fake_mark_failed,
    )
    monkeypatch.setattr(
        adp_crud,
        "release_discovery_nodes",
        fake_release_nodes,
    )
    monkeypatch.setattr(discovery_service.settings, "ADP_CRAWL_ENABLED", True)
    monkeypatch.setattr(
        discovery_service.settings,
        "ADP_CRAWL_SEASONS",
        "2026,2025",
    )
    monkeypatch.setattr(discovery_service.settings, "ADP_MAX_NEW_LEAGUES_PER_RUN", 1)
    monkeypatch.setattr(discovery_service.settings, "ADP_MAX_REQUESTS_PER_RUN", 10)
    monkeypatch.setattr(discovery_service.settings, "ADP_MAX_DISCOVERY_DEPTH", 2)
    monkeypatch.setattr(discovery_service.settings, "ADP_MAX_NODES_PER_RUN", 10)
    monkeypatch.setattr(discovery_service.settings, "ADP_MAX_RUNTIME_SECONDS", 300)
    monkeypatch.setattr(discovery_service.settings, "ADP_PROCESSING_TIMEOUT_SECONDS", 900)

    result = asyncio.run(
        discovery_service.process_adp_discovery_batch(
            FakeDB(),
            FakeSleeperClient(),
        )
    )

    assert result.discovered_league_count == 1
    assert len(captured_rows) == 1
    assert captured_rows[0]["node_type"] == "league_id"
    assert captured_rows[0]["source_type"] == "user_id"


def test_process_discovery_batch_releases_unprocessed_nodes_on_budget_stop(
    monkeypatch,
):
    released_ids: list[str] = []

    async def fake_claim_discovery_nodes(*args, **kwargs):
        return [
            SimpleNamespace(
                id="league-node-1",
                node_type="league_id",
                node_value="league-1",
                discovery_depth=0,
            ),
            SimpleNamespace(
                id="league-node-2",
                node_type="league_id",
                node_value="league-2",
                discovery_depth=0,
            ),
        ]

    async def fake_mark_processed(*args, **kwargs):
        return None

    async def fake_mark_failed(*args, **kwargs):
        return None

    async def fake_release_nodes(db, *, node_ids):
        released_ids.extend(node_ids)

    async def fake_enqueue_discovery_nodes(*args, **kwargs):
        return 0

    monkeypatch.setattr(
        adp_crud,
        "claim_discovery_nodes",
        fake_claim_discovery_nodes,
    )
    monkeypatch.setattr(
        adp_crud,
        "enqueue_discovery_nodes",
        fake_enqueue_discovery_nodes,
    )
    monkeypatch.setattr(
        adp_crud,
        "mark_discovery_node_processed",
        fake_mark_processed,
    )
    monkeypatch.setattr(
        adp_crud,
        "mark_discovery_node_failed",
        fake_mark_failed,
    )
    monkeypatch.setattr(
        adp_crud,
        "release_discovery_nodes",
        fake_release_nodes,
    )
    monkeypatch.setattr(discovery_service.settings, "ADP_CRAWL_ENABLED", True)
    monkeypatch.setattr(discovery_service.settings, "ADP_MAX_REQUESTS_PER_RUN", 1)
    monkeypatch.setattr(discovery_service.settings, "ADP_MAX_NEW_USERS_PER_RUN", 10)
    monkeypatch.setattr(discovery_service.settings, "ADP_MAX_NEW_DRAFTS_PER_RUN", 10)
    monkeypatch.setattr(discovery_service.settings, "ADP_MAX_NEW_LEAGUES_PER_RUN", 10)
    monkeypatch.setattr(discovery_service.settings, "ADP_MAX_DISCOVERY_DEPTH", 2)
    monkeypatch.setattr(discovery_service.settings, "ADP_MAX_NODES_PER_RUN", 10)
    monkeypatch.setattr(discovery_service.settings, "ADP_MAX_RUNTIME_SECONDS", 300)
    monkeypatch.setattr(discovery_service.settings, "ADP_PROCESSING_TIMEOUT_SECONDS", 900)

    result = asyncio.run(
        discovery_service.process_adp_discovery_batch(
            FakeDB(),
            FakeSleeperClient(),
        )
    )

    assert result.processed_node_count == 1
    assert result.stopped_reason == "request_budget_reached"
    assert released_ids == ["league-node-2"]
