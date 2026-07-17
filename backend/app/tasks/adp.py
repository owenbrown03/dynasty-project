from app.core.broker import broker
from app.core.database import AsyncSessionLocal
from app.integrations.sleeper.singleton import get_worker_sleeper_client
from app.services.adp.ingestion import ingest_existing_league_drafts


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
