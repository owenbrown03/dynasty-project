from fastapi import APIRouter, Query

from app.analytics.war.redraft.service import WARService
from app.api.deps import ContextDep
from app.core.config import settings
from app.crud import adp as adp_crud
from app.crud.fc.sync import sync_fantasycalc_values
from app.crud.ktc.sync import sync_ktc_values
from app.crud.underdog.sync import sync_underdog_adp
from app.crud.value import get_player_values
from app.integrations.sleeper.schemas.api import Projection
from app.services.dashboard.service import get_user_dashboard
from app.services.adp.discovery import (
    process_adp_discovery_batch,
    seed_manual_adp_discovery,
    seed_existing_leagues_for_adp_discovery,
    seed_existing_users_for_adp_discovery,
)
from app.services.adp.ingestion import (
    ingest_discovered_drafts,
    ingest_draft_by_id,
    ingest_existing_league_drafts,
    requalify_stored_drafts,
)
from app.services.adp.maintenance import run_adp_maintenance
from app.services.adp.report import (
    build_adp_dataset_report,
    get_adp_discovery_status,
)
from app.services.adp.service import invalidate_adp_cache
from app.services.adp.snapshots import (
    build_default_adp_snapshot_requests,
)
from app.schemas.adp import ADPFilters
from app.schemas.adp import (
    ADPDatasetReport,
    ADPDiscoveryStatusResponse,
    ADPMaintenanceRunResponse,
)
from app.schemas.league import LeagueOverviewItem
from app.services.leagues.details import LeagueDetails
from app.services.leagues.overview import get_league_overview
from app.services.sleeper.projection import sync_projections

router = APIRouter()

@router.get(
    "/projections",
    response_model=Projection,
)
async def test_projections(
    ctx: ContextDep,
):
    projections = await ctx.sleeper.read.get_projections(
        2026
    )

    return {
        "projections": projections[:10]
    }

@router.post("/sync-projections")
async def sync_projection_endpoint(
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

@router.get("/war")
async def test_war(
    ctx: ContextDep,
):
    results = await WARService().calculate(
        ctx.db,
        league_id="1312499253972602880",
    )

    # 1312145367281700864 14 team best ball
    # 1312499253972602880 12 team best ball
    
    return [
        {
            "name": r.name,
            "position": r.position,
            "team": r.team,
            "projection": r.projection,
            
            "starter_war": r.starter_war,
            "starter_replacement": r.starter_replacement,
            
            "roster_war": r.roster_war,
            "roster_replacement": r.roster_replacement,
        }
        #for r in (results[:500])
        for r in (results[:50] + results[250:300])
    ]

@router.get("/ktc_sync")
async def ktc_sync(
    ctx: ContextDep,
):
    return await sync_ktc_values(
        db=ctx.db,
        ktc=ctx.ktc
    )

@router.get("/underdog_sync")
async def underdog_sync(
    ctx: ContextDep,
):
    return await sync_underdog_adp(
        db=ctx.db,
        underdog=ctx.underdog
    )

@router.get("/fc_sync")
async def fc_sync(
    ctx: ContextDep,
):
    return await sync_fantasycalc_values(
        db=ctx.db,
        fc=ctx.fc
    )

@router.get("/dynasty_phase5")
async def dynasty_phase5(
    ctx: ContextDep,
):
    league_id = "1312499253972602880"

    war_players = await WARService().calculate(
        ctx.db,
        ctx.redis,
        league_id=league_id,
    )

    values = await get_player_values(
        ctx.db,
        player_ids=[
            p.player_id 
            for p in war_players
        ],
        war_players=war_players,
    )

    values.sort(
        key=lambda x: x.roster_war or 0,
        reverse=True,
    )

    return values[:50]

@router.get(
    "/league_overview/{username}",
    response_model=list[LeagueOverviewItem],
)
async def league_overview(
    username: str,
    ctx: ContextDep,
):
    return await get_league_overview(
        ctx.db,
        username=username,
    )

@router.get("/league_details/{league_id}")
async def league_details(
    league_id: str,
    ctx: ContextDep,
):
    return await LeagueDetails().get_league_details(
        ctx.db,
        ctx.redis,
        league_id=league_id,
    )

@router.get("/dashboard/{username}")
async def dashboard(
    username: str,
    ctx: ContextDep,
):
    return await get_user_dashboard(
        ctx.db,
        ctx.redis,
        username,
    )


@router.get(
    "/adp/report",
    response_model=ADPDatasetReport,
)
async def adp_report(
    ctx: ContextDep,
):
    return await build_adp_dataset_report(
        ctx.db,
    )


@router.get(
    "/adp/discovery/status",
    response_model=ADPDiscoveryStatusResponse,
)
async def adp_discovery_status(
    ctx: ContextDep,
    limit: int = Query(default=50, ge=1, le=500),
):
    return await get_adp_discovery_status(
        ctx.db,
        limit=limit,
    )


@router.post("/adp/discovery/seed")
async def adp_seed_discovery(
    ctx: ContextDep,
    limit: int | None = Query(default=None, ge=1),
    source: str = Query(default="leagues"),
    username: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    league_id: str | None = Query(default=None),
    draft_id: str | None = Query(default=None),
):
    if username or user_id or league_id or draft_id:
        return await seed_manual_adp_discovery(
            ctx.db,
            ctx.sleeper,
            username=username,
            user_id=user_id,
            league_id=league_id,
            draft_id=draft_id,
        )

    if source == "users":
        inserted_count = await seed_existing_users_for_adp_discovery(
            ctx.db,
            limit=limit,
        )
    elif source == "both":
        league_inserted_count = await seed_existing_leagues_for_adp_discovery(
            ctx.db,
            limit=limit,
        )
        user_inserted_count = await seed_existing_users_for_adp_discovery(
            ctx.db,
            limit=limit,
        )
        inserted_count = league_inserted_count + user_inserted_count
    else:
        inserted_count = await seed_existing_leagues_for_adp_discovery(
            ctx.db,
            limit=limit,
        )
    return {
        "inserted_count": inserted_count,
    }


@router.post("/adp/discovery/process")
async def adp_process_discovery(
    ctx: ContextDep,
    max_nodes: int | None = Query(default=None, ge=1),
    allow_when_disabled: bool = Query(default=True),
    discover_users: bool = Query(default=True),
):
    return await process_adp_discovery_batch(
        ctx.db,
        ctx.sleeper,
        max_nodes=max_nodes,
        allow_when_disabled=allow_when_disabled,
        discover_users=discover_users,
    )


@router.post("/adp/discovery/ingest")
async def adp_ingest_discovered(
    ctx: ContextDep,
    max_drafts: int = Query(default=25, ge=1, le=500),
):
    results = await ingest_discovered_drafts(
        ctx.db,
        ctx.sleeper,
        max_drafts=max_drafts,
    )
    return {
        "draft_count": len(results),
        "results": [
            {
                "draft_id": result.draft_id,
                "league_id": result.league_id,
                "pick_count": result.pick_count,
                "inserted_pick_count": result.inserted_pick_count,
                "is_qualified": result.is_qualified,
                "qualification_code": result.qualification_code,
            }
            for result in results
        ],
    }


@router.post(
    "/adp/sync-pending",
    response_model=ADPMaintenanceRunResponse,
)
async def adp_sync_pending(
    ctx: ContextDep,
    seed_source: str = Query(default="none"),
    seed_limit: int | None = Query(default=None, ge=1),
    cycles: int = Query(default=3, ge=1, le=20),
    max_nodes_per_cycle: int = Query(default=50, ge=1, le=200),
    max_drafts_per_cycle: int = Query(default=200, ge=1, le=500),
    allow_when_disabled: bool = Query(default=True),
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
        allow_when_disabled=allow_when_disabled,
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


@router.post("/adp/drafts/{draft_id}/ingest")
async def adp_ingest_draft(
    ctx: ContextDep,
    draft_id: str,
):
    result = await ingest_draft_by_id(
        ctx.db,
        ctx.sleeper,
        draft_id=draft_id,
    )
    return {
        "draft_id": result.draft_id,
        "league_id": result.league_id,
        "pick_count": result.pick_count,
        "inserted_pick_count": result.inserted_pick_count,
        "is_qualified": result.is_qualified,
        "qualification_code": result.qualification_code,
    }


@router.post("/adp/validation/existing-leagues")
async def adp_validate_existing_leagues(
    ctx: ContextDep,
    limit: int = Query(default=10, ge=1, le=500),
):
    ingestion_result = await ingest_existing_league_drafts(
        ctx.db,
        ctx.sleeper,
        max_leagues=limit,
    )
    report = await build_adp_dataset_report(
        ctx.db,
    )
    return {
        "ingestion": {
            "processed_league_count": ingestion_result.processed_league_count,
            "processed_draft_count": ingestion_result.processed_draft_count,
            "qualified_draft_count": ingestion_result.qualified_draft_count,
            "failed_draft_ids": ingestion_result.failed_draft_ids,
        },
        "report": report,
    }


@router.post("/adp/requalify")
async def adp_requalify_stored(
    ctx: ContextDep,
    limit: int = Query(default=100, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
    season: str | None = Query(default=None),
):
    result = await requalify_stored_drafts(
        ctx.db,
        limit=limit,
        offset=offset,
        season=season,
    )
    return {
        "processed_draft_count": result.processed_draft_count,
        "qualified_draft_count": result.qualified_draft_count,
        "reclassified_count": result.reclassified_count,
        "failed_draft_ids": result.failed_draft_ids,
    }


@router.post("/adp/validation/one-hop")
async def adp_validate_one_hop(
    ctx: ContextDep,
    seed_limit: int = Query(default=100, ge=1, le=5000),
    max_nodes: int = Query(default=100, ge=1, le=5000),
    max_drafts: int = Query(default=100, ge=1, le=5000),
):
    seeded = await seed_existing_leagues_for_adp_discovery(
        ctx.db,
        limit=seed_limit,
    )
    discovery = await process_adp_discovery_batch(
        ctx.db,
        ctx.sleeper,
        max_nodes=max_nodes,
        allow_when_disabled=True,
    )
    ingested = await ingest_discovered_drafts(
        ctx.db,
        ctx.sleeper,
        max_drafts=max_drafts,
    )
    report = await build_adp_dataset_report(
        ctx.db,
    )
    return {
        "seeded_count": seeded,
        "discovery": {
            "claimed_node_count": discovery.claimed_node_count,
            "processed_node_count": discovery.processed_node_count,
            "discovered_user_count": discovery.discovered_user_count,
            "discovered_league_count": discovery.discovered_league_count,
            "discovered_draft_count": discovery.discovered_draft_count,
            "request_count": discovery.request_count,
            "stopped_reason": discovery.stopped_reason,
        },
        "ingestion": {
            "draft_count": len(ingested),
            "qualified_draft_count": sum(
                1 for result in ingested if result.is_qualified
            ),
            "results": [
                {
                    "draft_id": result.draft_id,
                    "league_id": result.league_id,
                    "qualification_code": result.qualification_code,
                    "is_qualified": result.is_qualified,
                }
                for result in ingested
            ],
        },
        "report": report,
    }


@router.post("/adp/snapshots/refresh")
async def adp_refresh_snapshot(
    ctx: ContextDep,
    season: str | None = Query(default=None),
    draft_kind: str | None = Query(default=None),
    qb_format: str | None = Query(default=None),
    te_premium: str | None = Query(default=None),
    team_count: int | None = Query(default=None, ge=1, le=32),
    scoring_format: str | None = Query(default=None),
    minimum_draft_count: int = Query(default=5, ge=1, le=500),
):
    filters = ADPFilters(
        season=season,
        draft_kind=draft_kind,
        qb_format=qb_format,
        te_premium=te_premium,
        team_count=team_count,
        scoring_format=scoring_format,
        minimum_draft_count=minimum_draft_count,
    )
    snapshot = await adp_crud.create_adp_snapshot(
        ctx.db,
        season=filters.season,
        draft_kind=filters.draft_kind,
        qb_format=filters.qb_format,
        te_premium=filters.te_premium,
        team_count=filters.team_count,
        scoring_format=filters.scoring_format,
        minimum_draft_count=filters.minimum_draft_count,
    )
    await ctx.db.commit()
    await invalidate_adp_cache(
        ctx.redis,
        filters=filters,
    )
    return {
        "snapshot_id": snapshot.snapshot_id,
        "draft_count": snapshot.sample.draft_count,
        "pick_count": snapshot.sample.pick_count,
        "player_count": len(snapshot.players),
        "generated_at": snapshot.sample.generated_at,
    }


@router.post("/adp/snapshots/refresh-defaults")
async def adp_refresh_default_snapshots(
    ctx: ContextDep,
    seasons: str | None = Query(default=None),
    minimum_draft_count: int = Query(default=5, ge=1, le=500),
):
    requested_seasons = (
        [
            season.strip()
            for season in seasons.split(",")
            if season.strip()
        ]
        if seasons
        else settings.adp_crawl_seasons
    )
    requests = build_default_adp_snapshot_requests(
        seasons=requested_seasons,
        minimum_draft_count=minimum_draft_count,
    )
    results: list[dict[str, object]] = []
    skipped_count = 0

    for request in requests:
        filters = ADPFilters(
            season=request.season,
            draft_kind=request.draft_kind,
            qb_format=request.qb_format,
            te_premium=request.te_premium,
            team_count=request.team_count,
            minimum_draft_count=request.minimum_draft_count,
        )
        snapshot = await adp_crud.create_adp_snapshot(
            ctx.db,
            season=filters.season,
            draft_kind=filters.draft_kind,
            qb_format=filters.qb_format,
            te_premium=filters.te_premium,
            team_count=filters.team_count,
            minimum_draft_count=filters.minimum_draft_count,
            skip_empty=True,
        )
        if snapshot is None:
            skipped_count += 1
            continue
        await ctx.db.commit()
        await invalidate_adp_cache(
            ctx.redis,
            filters=filters,
        )
        results.append(
            {
                "snapshot_id": snapshot.snapshot_id,
                "season": request.season,
                "draft_kind": request.draft_kind,
                "qb_format": request.qb_format,
                "te_premium": request.te_premium,
                "team_count": request.team_count,
                "draft_count": snapshot.sample.draft_count,
                "player_count": len(snapshot.players),
            }
        )

    return {
        "snapshot_count": len(results),
        "skipped_count": skipped_count,
        "results": results,
    }
