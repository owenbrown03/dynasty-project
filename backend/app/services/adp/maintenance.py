from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.sleeper.client import SleeperClient
from app.services.adp.discovery import (
    ADPDiscoveryBatchResult,
    process_adp_discovery_batch,
    seed_existing_leagues_for_adp_discovery,
    seed_existing_users_for_adp_discovery,
)
from app.services.adp.ingestion import (
    DraftIngestionResult,
    ingest_discovered_drafts,
)


@dataclass(frozen=True)
class ADPMaintenanceCycleResult:
    discovery: ADPDiscoveryBatchResult
    ingested_drafts: list[DraftIngestionResult]


@dataclass(frozen=True)
class ADPMaintenanceRunResult:
    seeded_count: int
    completed_cycles: int
    total_processed_nodes: int
    total_discovered_users: int
    total_discovered_leagues: int
    total_discovered_drafts: int
    total_requests: int
    total_ingested_drafts: int
    total_qualified_drafts: int
    stopped_reason: str | None
    cycle_results: list[ADPMaintenanceCycleResult]


async def _seed_adp_discovery(
    db: AsyncSession,
    *,
    seed_source: str,
    seed_limit: int | None,
) -> int:
    if seed_source == "none":
        return 0

    if seed_source == "users":
        return await seed_existing_users_for_adp_discovery(
            db,
            limit=seed_limit,
        )

    if seed_source == "both":
        league_count = await seed_existing_leagues_for_adp_discovery(
            db,
            limit=seed_limit,
        )
        user_count = await seed_existing_users_for_adp_discovery(
            db,
            limit=seed_limit,
        )
        return league_count + user_count

    return await seed_existing_leagues_for_adp_discovery(
        db,
        limit=seed_limit,
    )


async def run_adp_maintenance(
    db: AsyncSession,
    sleeper: SleeperClient,
    *,
    seed_source: str = "none",
    seed_limit: int | None = None,
    cycles: int = 1,
    max_nodes_per_cycle: int = 50,
    max_drafts_per_cycle: int = 200,
    allow_when_disabled: bool = False,
    discover_users: bool = False,
) -> ADPMaintenanceRunResult:
    seeded_count = await _seed_adp_discovery(
        db,
        seed_source=seed_source,
        seed_limit=seed_limit,
    )

    cycle_results: list[ADPMaintenanceCycleResult] = []
    total_processed_nodes = 0
    total_discovered_users = 0
    total_discovered_leagues = 0
    total_discovered_drafts = 0
    total_requests = 0
    total_ingested_drafts = 0
    total_qualified_drafts = 0
    stopped_reason: str | None = None

    for _ in range(max(cycles, 0)):
        discovery = await process_adp_discovery_batch(
            db,
            sleeper,
            max_nodes=max_nodes_per_cycle,
            allow_when_disabled=allow_when_disabled,
            discover_users=discover_users,
        )
        ingested_drafts = await ingest_discovered_drafts(
            db,
            sleeper,
            max_drafts=max_drafts_per_cycle,
        )
        cycle_results.append(
            ADPMaintenanceCycleResult(
                discovery=discovery,
                ingested_drafts=ingested_drafts,
            )
        )

        total_processed_nodes += discovery.processed_node_count
        total_discovered_users += discovery.discovered_user_count
        total_discovered_leagues += discovery.discovered_league_count
        total_discovered_drafts += discovery.discovered_draft_count
        total_requests += discovery.request_count
        total_ingested_drafts += len(ingested_drafts)
        total_qualified_drafts += sum(
            1
            for result in ingested_drafts
            if result.is_qualified
        )

        if discovery.stopped_reason == "crawl_disabled":
            stopped_reason = discovery.stopped_reason
            break

    if cycle_results:
        last_reason = cycle_results[-1].discovery.stopped_reason
        if last_reason is not None:
            stopped_reason = last_reason

    return ADPMaintenanceRunResult(
        seeded_count=seeded_count,
        completed_cycles=len(cycle_results),
        total_processed_nodes=total_processed_nodes,
        total_discovered_users=total_discovered_users,
        total_discovered_leagues=total_discovered_leagues,
        total_discovered_drafts=total_discovered_drafts,
        total_requests=total_requests,
        total_ingested_drafts=total_ingested_drafts,
        total_qualified_drafts=total_qualified_drafts,
        stopped_reason=stopped_reason,
        cycle_results=cycle_results,
    )
