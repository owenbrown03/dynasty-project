from __future__ import annotations

from app.crud import adp as adp_crud
from app.schemas.adp import (
    ADPDatasetReport,
    ADPDiscoveryStatus,
    ADPDiscoveryStatusResponse,
    ADPDistributionItem,
)


def _to_distribution_items(
    rows: list[adp_crud.ADPDistributionCount],
) -> list[ADPDistributionItem]:
    return [
        ADPDistributionItem(
            key=row.key,
            count=row.count,
        )
        for row in rows
    ]


async def build_adp_dataset_report(
    db,
) -> ADPDatasetReport:
    summary = await adp_crud.get_adp_dataset_report_row(
        db,
    )
    qualification_code_distribution = await adp_crud.get_adp_distribution(
        db,
        source="qualification_code",
    )
    draft_kind_distribution = await adp_crud.get_adp_distribution(
        db,
        source="draft_kind",
    )
    qb_format_distribution = await adp_crud.get_adp_distribution(
        db,
        source="qb_format",
    )
    te_premium_distribution = await adp_crud.get_adp_distribution(
        db,
        source="te_premium",
    )
    team_count_distribution = await adp_crud.get_adp_distribution(
        db,
        source="team_count",
    )
    discovery_depth_distribution = await adp_crud.get_adp_distribution(
        db,
        source="discovery_depth",
    )
    discovery_status_distribution = await adp_crud.get_adp_distribution(
        db,
        source="discovery_status",
    )

    return ADPDatasetReport(
        qualified_draft_count=summary.qualified_draft_count,
        excluded_draft_count=summary.excluded_draft_count,
        unique_league_count=summary.unique_league_count,
        unique_root_source_count=summary.unique_root_source_count,
        earliest_draft_at=summary.earliest_draft_at,
        latest_draft_at=summary.latest_draft_at,
        qualification_code_distribution=_to_distribution_items(
            qualification_code_distribution,
        ),
        draft_kind_distribution=_to_distribution_items(
            draft_kind_distribution,
        ),
        qb_format_distribution=_to_distribution_items(
            qb_format_distribution,
        ),
        te_premium_distribution=_to_distribution_items(
            te_premium_distribution,
        ),
        team_count_distribution=_to_distribution_items(
            team_count_distribution,
        ),
        discovery_depth_distribution=_to_distribution_items(
            discovery_depth_distribution,
        ),
        discovery_status_distribution=_to_distribution_items(
            discovery_status_distribution,
        ),
    )


async def get_adp_discovery_status(
    db,
    *,
    limit: int = 50,
) -> ADPDiscoveryStatusResponse:
    counts_by_status = await adp_crud.get_discovery_status_counts(
        db,
    )
    nodes = await adp_crud.get_recent_discovery_nodes(
        db,
        limit=limit,
    )
    return ADPDiscoveryStatusResponse(
        counts_by_status=_to_distribution_items(
            counts_by_status,
        ),
        nodes=[
            ADPDiscoveryStatus(
                node_type=node.node_type,
                node_value=node.node_value,
                source_type=node.source_type,
                source_value=node.source_value,
                discovery_depth=node.discovery_depth,
                status=node.status,
                attempt_count=node.attempt_count,
                next_retry_at=node.next_retry_at,
                last_checked_at=node.last_checked_at,
                failure_reason=node.failure_reason,
                updated_at=node.updated_at,
            )
            for node in nodes
        ],
    )
