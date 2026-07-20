from __future__ import annotations

import json

from app.core.config import settings
from app.crud import adp as adp_crud
from app.infrastructure.redis.client import RedisClient
from app.schemas.adp import (
    ADPDatasetReport,
    ADPDiscoveryStatus,
    ADPDiscoveryStatusResponse,
    ADPDistributionItem,
    ADPFilters,
    ADPMetadataResponse,
)

ADP_REPORT_CACHE_TTL_SECONDS = 5 * 60
ADP_METADATA_CACHE_TTL_SECONDS = 5 * 60
ADP_REPORT_CACHE_KEY = "adp:report"
ADP_METADATA_CACHE_PREFIX = "adp:metadata:"


def build_adp_report_cache_key() -> str:
    return ADP_REPORT_CACHE_KEY


def build_adp_metadata_cache_key(
    *,
    filters: ADPFilters,
) -> str:
    payload = filters.model_dump(mode="json")
    return ADP_METADATA_CACHE_PREFIX + json.dumps(
        payload,
        sort_keys=True,
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
    redis: RedisClient | None = None,
) -> ADPDatasetReport:
    if redis is not None:
        cached_payload = await redis.get(
            build_adp_report_cache_key(),
        )
        if cached_payload:
            return ADPDatasetReport.model_validate_json(
                cached_payload,
            )

    summary = await adp_crud.get_adp_dataset_report_row(
        db,
    )
    qualification_code_distribution = await adp_crud.get_adp_distribution(
        db,
        source="qualification_code",
    )
    season_distribution = await adp_crud.get_adp_distribution(
        db,
        source="season",
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
    scoring_format_distribution = await adp_crud.get_adp_distribution(
        db,
        source="scoring_format",
    )
    team_count_distribution = await adp_crud.get_adp_distribution(
        db,
        source="team_count",
    )
    discovery_source_distribution = await adp_crud.get_adp_distribution(
        db,
        source="discovery_source",
    )
    discovery_depth_distribution = await adp_crud.get_adp_distribution(
        db,
        source="discovery_depth",
    )
    discovery_status_distribution = await adp_crud.get_adp_distribution(
        db,
        source="discovery_status",
    )

    report = ADPDatasetReport(
        qualified_draft_count=summary.qualified_draft_count,
        excluded_draft_count=summary.excluded_draft_count,
        unique_league_count=summary.unique_league_count,
        unique_root_source_count=summary.unique_root_source_count,
        earliest_draft_at=summary.earliest_draft_at,
        latest_draft_at=summary.latest_draft_at,
        qualification_code_distribution=_to_distribution_items(
            qualification_code_distribution,
        ),
        season_distribution=_to_distribution_items(
            season_distribution,
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
        scoring_format_distribution=_to_distribution_items(
            scoring_format_distribution,
        ),
        team_count_distribution=_to_distribution_items(
            team_count_distribution,
        ),
        discovery_source_distribution=_to_distribution_items(
            discovery_source_distribution,
        ),
        discovery_depth_distribution=_to_distribution_items(
            discovery_depth_distribution,
        ),
        discovery_status_distribution=_to_distribution_items(
            discovery_status_distribution,
        ),
    )

    if redis is not None:
        await redis.set(
            build_adp_report_cache_key(),
            report.model_dump_json(),
            ttl_seconds=min(
                settings.ADP_CACHE_TTL_SECONDS,
                ADP_REPORT_CACHE_TTL_SECONDS,
            ),
        )

    return report


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


async def get_adp_metadata(
    db,
    *,
    filters: ADPFilters,
    redis: RedisClient | None = None,
) -> ADPMetadataResponse:
    if redis is not None:
        cached_payload = await redis.get(
            build_adp_metadata_cache_key(
                filters=filters,
            ),
        )
        if cached_payload:
            return ADPMetadataResponse.model_validate_json(
                cached_payload,
            )

    metadata = ADPMetadataResponse(
        season_options=_to_distribution_items(
            await adp_crud.get_filtered_adp_distribution(
                db,
                source="season",
                season=filters.season,
                draft_kind=filters.draft_kind,
                qb_format=filters.qb_format,
                te_premium=filters.te_premium,
                team_count=filters.team_count,
                scoring_format=filters.scoring_format,
                start_date=filters.start_date,
                end_date=filters.end_date,
            )
        ),
        draft_kind_options=_to_distribution_items(
            await adp_crud.get_filtered_adp_distribution(
                db,
                source="draft_kind",
                season=filters.season,
                draft_kind=filters.draft_kind,
                qb_format=filters.qb_format,
                te_premium=filters.te_premium,
                team_count=filters.team_count,
                scoring_format=filters.scoring_format,
                start_date=filters.start_date,
                end_date=filters.end_date,
            )
        ),
        qb_format_options=_to_distribution_items(
            await adp_crud.get_filtered_adp_distribution(
                db,
                source="qb_format",
                season=filters.season,
                draft_kind=filters.draft_kind,
                qb_format=filters.qb_format,
                te_premium=filters.te_premium,
                team_count=filters.team_count,
                scoring_format=filters.scoring_format,
                start_date=filters.start_date,
                end_date=filters.end_date,
            )
        ),
        te_premium_options=_to_distribution_items(
            await adp_crud.get_filtered_adp_distribution(
                db,
                source="te_premium",
                season=filters.season,
                draft_kind=filters.draft_kind,
                qb_format=filters.qb_format,
                te_premium=filters.te_premium,
                team_count=filters.team_count,
                scoring_format=filters.scoring_format,
                start_date=filters.start_date,
                end_date=filters.end_date,
            )
        ),
        team_count_options=_to_distribution_items(
            await adp_crud.get_filtered_adp_distribution(
                db,
                source="team_count",
                season=filters.season,
                draft_kind=filters.draft_kind,
                qb_format=filters.qb_format,
                te_premium=filters.te_premium,
                team_count=filters.team_count,
                scoring_format=filters.scoring_format,
                start_date=filters.start_date,
                end_date=filters.end_date,
            )
        ),
        scoring_format_options=_to_distribution_items(
            await adp_crud.get_filtered_adp_distribution(
                db,
                source="scoring_format",
                season=filters.season,
                draft_kind=filters.draft_kind,
                qb_format=filters.qb_format,
                te_premium=filters.te_premium,
                team_count=filters.team_count,
                scoring_format=filters.scoring_format,
                start_date=filters.start_date,
                end_date=filters.end_date,
            )
        ),
    )

    if redis is not None:
        await redis.set(
            build_adp_metadata_cache_key(
                filters=filters,
            ),
            metadata.model_dump_json(),
            ttl_seconds=min(
                settings.ADP_CACHE_TTL_SECONDS,
                ADP_METADATA_CACHE_TTL_SECONDS,
            ),
        )

    return metadata
