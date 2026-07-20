import asyncio
from datetime import UTC, datetime

from app.crud import adp as adp_crud
from app.services.adp.report import (
    build_adp_metadata_cache_key,
    build_adp_dataset_report,
    build_adp_report_cache_key,
    get_adp_metadata,
    get_adp_discovery_status,
)
from app.schemas.adp import ADPFilters


class FakeDB:
    pass


class FakeRedis:
    def __init__(self):
        self.values: dict[str, str] = {}
        self.writes: list[tuple[str, str, int | None]] = []

    async def get(self, key: str):
        return self.values.get(key)

    async def set(
        self,
        key: str,
        value: str,
        ttl_seconds: int | None = None,
    ):
        self.values[key] = value
        self.writes.append((key, value, ttl_seconds))


async def _summary_stub(*args, **kwargs):
    return adp_crud.ADPDatasetReportRow(
        qualified_draft_count=12,
        excluded_draft_count=5,
        unique_league_count=9,
        unique_root_source_count=4,
        earliest_draft_at=datetime(2026, 1, 1, tzinfo=UTC),
        latest_draft_at=datetime(2026, 7, 1, tzinfo=UTC),
    )


async def _distribution_stub(*args, **kwargs):
    source = kwargs["source"]
    return [
        adp_crud.ADPDistributionCount(
            key=f"{source}-a",
            count=2,
        ),
        adp_crud.ADPDistributionCount(
            key=f"{source}-b",
            count=1,
        ),
    ]


async def _status_counts_stub(*args, **kwargs):
    return [
        adp_crud.ADPDistributionCount(
            key="pending",
            count=3,
        ),
    ]


async def _recent_nodes_stub(*args, **kwargs):
    now = datetime(2026, 7, 17, tzinfo=UTC)
    return [
        type(
            "Node",
            (),
            {
                "node_type": "draft_id",
                "node_value": "draft-1",
                "source_type": "league_id",
                "source_value": "league-1",
                "discovery_depth": 1,
                "status": "processed",
                "attempt_count": 1,
                "next_retry_at": None,
                "last_checked_at": now,
                "failure_reason": None,
                "updated_at": now,
            },
        )(),
    ]


def test_build_adp_dataset_report(monkeypatch):
    monkeypatch.setattr(
        adp_crud,
        "get_adp_dataset_report_row",
        _summary_stub,
    )
    monkeypatch.setattr(
        adp_crud,
        "get_adp_distribution",
        _distribution_stub,
    )

    report = asyncio.run(
        build_adp_dataset_report(
            FakeDB(),
        )
    )

    assert report.qualified_draft_count == 12
    assert report.excluded_draft_count == 5
    assert report.unique_league_count == 9
    assert report.unique_root_source_count == 4
    assert report.earliest_draft_at == datetime(2026, 1, 1, tzinfo=UTC)
    assert report.latest_draft_at == datetime(2026, 7, 1, tzinfo=UTC)
    assert report.qualification_code_distribution[0].key == "qualification_code-a"
    assert report.season_distribution[0].key == "season-a"
    assert report.draft_kind_distribution[1].key == "draft_kind-b"
    assert report.qb_format_distribution[0].key == "qb_format-a"
    assert report.te_premium_distribution[1].key == "te_premium-b"
    assert report.scoring_format_distribution[0].key == "scoring_format-a"
    assert report.team_count_distribution[1].key == "team_count-b"
    assert report.discovery_source_distribution[0].key == "discovery_source-a"
    assert report.discovery_depth_distribution[1].key == "discovery_depth-b"
    assert report.discovery_status_distribution[1].key == "discovery_status-b"


def test_build_adp_dataset_report_uses_cache(monkeypatch):
    async def _fail_summary(*args, **kwargs):
        raise AssertionError("summary should not be called when cache exists")

    monkeypatch.setattr(
        adp_crud,
        "get_adp_dataset_report_row",
        _fail_summary,
    )

    cached_report = build_adp_dataset_report
    redis = FakeRedis()
    redis.values[build_adp_report_cache_key()] = (
        '{"qualified_draft_count":7,"excluded_draft_count":2,'
        '"unique_league_count":5,"unique_root_source_count":3,'
        '"earliest_draft_at":null,"latest_draft_at":null,'
        '"qualification_code_distribution":[],"season_distribution":[],'
        '"draft_kind_distribution":[],"qb_format_distribution":[],'
        '"te_premium_distribution":[],"scoring_format_distribution":[],'
        '"team_count_distribution":[],"discovery_source_distribution":[],'
        '"discovery_depth_distribution":[],"discovery_status_distribution":[]}'
    )

    report = asyncio.run(
        cached_report(
            FakeDB(),
            redis=redis,
        )
    )

    assert report.qualified_draft_count == 7
    assert report.unique_root_source_count == 3


def test_get_adp_discovery_status(monkeypatch):
    monkeypatch.setattr(
        adp_crud,
        "get_discovery_status_counts",
        _status_counts_stub,
    )
    monkeypatch.setattr(
        adp_crud,
        "get_recent_discovery_nodes",
        _recent_nodes_stub,
    )

    status = asyncio.run(
        get_adp_discovery_status(
            FakeDB(),
            limit=25,
        )
    )

    assert status.counts_by_status[0].key == "pending"
    assert status.nodes[0].node_value == "draft-1"
    assert status.nodes[0].status == "processed"


def test_get_adp_metadata(monkeypatch):
    monkeypatch.setattr(
        adp_crud,
        "get_filtered_adp_distribution",
        _distribution_stub,
    )

    metadata = asyncio.run(
        get_adp_metadata(
            FakeDB(),
            filters=ADPFilters(
                season="2026",
                draft_kind="startup",
                qb_format="superflex",
            ),
        )
    )

    assert metadata.season_options[0].key == "season-a"
    assert metadata.draft_kind_options[0].key == "draft_kind-a"
    assert metadata.team_count_options[1].key == "team_count-b"


def test_adp_filters_normalize_blank_strings():
    filters = ADPFilters(
        season=" 2026 ",
        draft_kind="startup",
        qb_format="superflex",
        te_premium="",
        scoring_format="   ",
    )

    assert filters.season == "2026"
    assert filters.te_premium is None
    assert filters.scoring_format is None


def test_get_adp_metadata_uses_cache(monkeypatch):
    async def _fail_distribution(*args, **kwargs):
        raise AssertionError("distribution query should not be called when cache exists")

    monkeypatch.setattr(
        adp_crud,
        "get_filtered_adp_distribution",
        _fail_distribution,
    )

    filters = ADPFilters(
        season="2026",
        draft_kind="startup",
        qb_format="superflex",
    )
    redis = FakeRedis()
    redis.values[build_adp_metadata_cache_key(filters=filters)] = (
        '{"season_options":[{"key":"2026","count":4}],"draft_kind_options":[],'
        '"qb_format_options":[],"te_premium_options":[],'
        '"team_count_options":[],"scoring_format_options":[]}'
    )

    metadata = asyncio.run(
        get_adp_metadata(
            FakeDB(),
            filters=filters,
            redis=redis,
        )
    )

    assert metadata.season_options[0].key == "2026"
