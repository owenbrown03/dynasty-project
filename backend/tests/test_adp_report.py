import asyncio
from datetime import UTC, datetime

from app.crud import adp as adp_crud
from app.services.adp.report import (
    build_adp_dataset_report,
    get_adp_metadata,
    get_adp_discovery_status,
)
from app.schemas.adp import ADPFilters


class FakeDB:
    pass


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
    assert report.qualification_code_distribution[0].key == "qualification_code-a"
    assert report.discovery_status_distribution[1].key == "discovery_status-b"


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
