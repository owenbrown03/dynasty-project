from app.core.broker import broker
from app.core.database import AsyncSessionLocal
from app.integrations.sleeper.singleton import get_worker_sleeper_client
from app.services.adp.discovery import (
    process_adp_discovery_batch,
    seed_existing_leagues_for_adp_discovery,
)
from app.crud import adp as adp_crud
from app.services.adp.ingestion import (
    ingest_discovered_drafts,
    ingest_existing_league_drafts,
)


@broker.task
async def ingest_existing_league_drafts_task(
    max_leagues: int | None = None,
):
    async with AsyncSessionLocal() as db:
        sleeper = await get_worker_sleeper_client()
        result = await ingest_existing_league_drafts(
            db,
            sleeper,
            max_leagues=max_leagues,
        )
        return {
            "processed_league_count": result.processed_league_count,
            "processed_draft_count": result.processed_draft_count,
            "qualified_draft_count": result.qualified_draft_count,
            "failed_draft_ids": result.failed_draft_ids,
        }


@broker.task
async def seed_existing_leagues_for_adp_discovery_task(
    limit: int | None = None,
):
    async with AsyncSessionLocal() as db:
        inserted = await seed_existing_leagues_for_adp_discovery(
            db,
            limit=limit,
        )
        return {
            "inserted_count": inserted,
        }


@broker.task
async def process_adp_discovery_batch_task(
    max_nodes: int | None = None,
):
    async with AsyncSessionLocal() as db:
        sleeper = await get_worker_sleeper_client()
        result = await process_adp_discovery_batch(
            db,
            sleeper,
            max_nodes=max_nodes,
        )
        return {
            "claimed_node_count": result.claimed_node_count,
            "processed_node_count": result.processed_node_count,
            "discovered_user_count": result.discovered_user_count,
            "discovered_league_count": result.discovered_league_count,
            "discovered_draft_count": result.discovered_draft_count,
            "request_count": result.request_count,
            "stopped_reason": result.stopped_reason,
        }


@broker.task
async def ingest_discovered_adp_drafts_task(
    max_drafts: int | None = None,
):
    async with AsyncSessionLocal() as db:
        sleeper = await get_worker_sleeper_client()
        results = await ingest_discovered_drafts(
            db,
            sleeper,
            max_drafts=max_drafts or 25,
        )
        return [
            {
                "draft_id": result.draft_id,
                "league_id": result.league_id,
                "pick_count": result.pick_count,
                "inserted_pick_count": result.inserted_pick_count,
                "is_qualified": result.is_qualified,
                "qualification_code": result.qualification_code,
            }
            for result in results
        ]


@broker.task
async def refresh_adp_snapshot_task(
    season: str | None = None,
    draft_kind: str | None = None,
    qb_format: str | None = None,
    te_premium: str | None = None,
    team_count: int | None = None,
    scoring_format: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    minimum_draft_count: int = 5,
):
    from datetime import datetime

    async with AsyncSessionLocal() as db:
        snapshot = await adp_crud.create_adp_snapshot(
            db,
            season=season,
            draft_kind=draft_kind,
            qb_format=qb_format,
            te_premium=te_premium,
            team_count=team_count,
            scoring_format=scoring_format,
            start_date=(
                datetime.fromisoformat(start_date)
                if start_date
                else None
            ),
            end_date=(
                datetime.fromisoformat(end_date)
                if end_date
                else None
            ),
            minimum_draft_count=minimum_draft_count,
        )
        await db.commit()
        return {
            "snapshot_id": snapshot.snapshot_id,
            "draft_count": snapshot.sample.draft_count,
            "pick_count": snapshot.sample.pick_count,
            "player_count": len(snapshot.players),
            "generated_at": snapshot.sample.generated_at.isoformat()
            if snapshot.sample.generated_at
            else None,
        }
