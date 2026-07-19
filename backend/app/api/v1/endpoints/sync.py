from fastapi import APIRouter, Query

from app.api.deps import ContextDep
from app.crud.fc.sync import sync_fantasycalc_values
from app.crud.ktc.sync import sync_ktc_values
from app.crud.underdog.sync import sync_underdog_adp
from app.schemas.adp import ADPMaintenanceRunResponse
from app.services.adp.maintenance import run_adp_maintenance
from app.services.sleeper.projection import sync_projections

router = APIRouter()

@router.post("/sleeper-projections")
async def sleeper_projections_endpoint(
    ctx: ContextDep,
):
    await sync_projections(
        db=ctx.db,
        sleeper=ctx.sleeper,
        season=2026,
        force_update=True,
    )

    return {
        "status": "complete"
    }

@router.get("/ktc")
async def ktc_endpoint(
    ctx: ContextDep,
):
    return await sync_ktc_values(
        db=ctx.db,
        ktc=ctx.ktc
    )

@router.get("/underdog")
async def underdog_endpoint(
    ctx: ContextDep,
):
    return await sync_underdog_adp(
        db=ctx.db,
        underdog=ctx.underdog
    )

@router.get("/fc")
async def fc_endpoint(
    ctx: ContextDep,
):
    return await sync_fantasycalc_values(
        db=ctx.db,
        fc=ctx.fc
    )


@router.post(
    "/adp",
    response_model=ADPMaintenanceRunResponse,
)
async def adp_sync_endpoint(
    ctx: ContextDep,
    seed_source: str = Query(default="none"),
    seed_limit: int | None = Query(default=None, ge=1),
    cycles: int = Query(default=3, ge=1, le=20),
    max_nodes_per_cycle: int = Query(default=50, ge=1, le=200),
    max_drafts_per_cycle: int = Query(default=200, ge=1, le=500),
    discover_users: bool = Query(default=False),
):
    result = await run_adp_maintenance(
        ctx.db,
        ctx.sleeper,
        seed_source=seed_source,
        seed_limit=seed_limit,
        cycles=cycles,
        max_nodes_per_cycle=max_nodes_per_cycle,
        max_drafts_per_cycle=max_drafts_per_cycle,
        allow_when_disabled=True,
        discover_users=discover_users,
    )
    return ADPMaintenanceRunResponse(
        seeded_count=result.seeded_count,
        completed_cycles=result.completed_cycles,
        total_processed_nodes=result.total_processed_nodes,
        total_discovered_users=result.total_discovered_users,
        total_discovered_leagues=result.total_discovered_leagues,
        total_discovered_drafts=result.total_discovered_drafts,
        total_requests=result.total_requests,
        total_ingested_drafts=result.total_ingested_drafts,
        total_qualified_drafts=result.total_qualified_drafts,
        stopped_reason=result.stopped_reason,
        cycles=[
            {
                "claimed_node_count": cycle.discovery.claimed_node_count,
                "processed_node_count": cycle.discovery.processed_node_count,
                "discovered_user_count": cycle.discovery.discovered_user_count,
                "discovered_league_count": cycle.discovery.discovered_league_count,
                "discovered_draft_count": cycle.discovery.discovered_draft_count,
                "request_count": cycle.discovery.request_count,
                "stopped_reason": cycle.discovery.stopped_reason,
                "ingested_draft_count": len(cycle.ingested_drafts),
                "qualified_draft_count": sum(
                    1
                    for item in cycle.ingested_drafts
                    if item.is_qualified
                ),
            }
            for cycle in result.cycle_results
        ],
    )
