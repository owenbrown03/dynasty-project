import asyncio
from types import SimpleNamespace

from app.crud import adp as adp_crud
from app.services.adp import ingestion as ingestion_service


class FakeDB:
    def __init__(self):
        self.commits = 0

    async def commit(self):
        self.commits += 1


class FakeSleeperRead:
    def __init__(self):
        self.requested_draft_ids: list[str] = []
        self.requested_league_ids: list[str] = []

    async def get_draft(self, draft_id: str):
        self.requested_draft_ids.append(draft_id)
        return SimpleNamespace(
            draft_id=draft_id,
            league_id="league-1",
            season="2026",
        )

    async def get_league(self, league_id: str):
        self.requested_league_ids.append(league_id)
        class FakeLeague:
            def model_dump(self_inner):
                return {
                    "league_id": league_id,
                    "name": "League One",
                    "avatar": None,
                    "season": "2026",
                    "status": "complete",
                    "total_rosters": 12,
                    "draft_id": "draft-1",
                    "previous_league_id": None,
                    "metadata": {},
                    "settings": {"type": 2},
                    "scoring_settings": {"rec": 1.0},
                    "roster_positions": [
                        "QB",
                        "RB",
                        "RB",
                        "WR",
                        "WR",
                        "TE",
                        "FLEX",
                        "BN",
                    ],
                }

        return FakeLeague()


class FakeSleeperClient:
    def __init__(self):
        self.read = FakeSleeperRead()


def test_ingest_draft_by_id_hydrates_missing_league(monkeypatch):
    captured_upsert_rows: list[dict] = []
    captured_ingest_inputs: list[tuple[str, str]] = []

    async def fake_get_leagues_by_ids(*args, **kwargs):
        return {}

    async def fake_upsert_leagues(db, rows):
        captured_upsert_rows.extend(rows)

    async def fake_ingest_draft(db, sleeper, *, league, draft):
        captured_ingest_inputs.append(
            (league.league_id, draft.draft_id),
        )
        return ingestion_service.DraftIngestionResult(
            draft_id=draft.draft_id,
            league_id=league.league_id,
            pick_count=0,
            inserted_pick_count=0,
            is_qualified=False,
            qualification_code="unknown_format",
        )

    monkeypatch.setattr(
        adp_crud,
        "get_leagues_by_ids",
        fake_get_leagues_by_ids,
    )
    monkeypatch.setattr(
        adp_crud,
        "upsert_leagues",
        fake_upsert_leagues,
    )
    monkeypatch.setattr(
        ingestion_service,
        "ingest_draft",
        fake_ingest_draft,
    )

    result = asyncio.run(
        ingestion_service.ingest_draft_by_id(
            FakeDB(),
            FakeSleeperClient(),
            draft_id="draft-1",
        )
    )

    assert result.draft_id == "draft-1"
    assert captured_ingest_inputs == [("league-1", "draft-1")]
    assert captured_upsert_rows
    assert captured_upsert_rows[0]["league_id"] == "league-1"


def test_ingest_discovered_drafts_batches_ready_seeds(monkeypatch):
    db = FakeDB()
    ingested_ids: list[str] = []

    async def fake_get_ready_discovered_draft_ids(*args, **kwargs):
        return [
            adp_crud.ADPDraftIngestionSeed(
                draft_id="draft-1",
                source_type="league_id",
                source_value="league-1",
            ),
            adp_crud.ADPDraftIngestionSeed(
                draft_id="draft-2",
                source_type="league_id",
                source_value="league-2",
            ),
        ]

    async def fake_ingest_draft_by_id(db, sleeper, *, draft_id):
        ingested_ids.append(draft_id)
        return ingestion_service.DraftIngestionResult(
            draft_id=draft_id,
            league_id=f"{draft_id}-league",
            pick_count=24,
            inserted_pick_count=24,
            is_qualified=True,
            qualification_code="qualified",
        )

    monkeypatch.setattr(
        adp_crud,
        "get_ready_discovered_draft_ids",
        fake_get_ready_discovered_draft_ids,
    )
    monkeypatch.setattr(
        ingestion_service,
        "ingest_draft_by_id",
        fake_ingest_draft_by_id,
    )

    results = asyncio.run(
        ingestion_service.ingest_discovered_drafts(
            db,
            FakeSleeperClient(),
            max_drafts=5,
        )
    )

    assert ingested_ids == ["draft-1", "draft-2"]
    assert db.commits == 1
    assert len(results) == 2
    assert results[0].qualification_code == "qualified"
