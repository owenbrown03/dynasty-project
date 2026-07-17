from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import adp as adp_crud
from app.integrations.sleeper.client import SleeperClient
from app.models.db.adp import ADPDraftQualification
from app.models.db.sleeper.api import League
from app.services.adp.classification import classify_draft
from app.services.sleeper import transformers


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DraftIngestionResult:
    draft_id: str
    league_id: str | None
    pick_count: int
    inserted_pick_count: int
    is_qualified: bool
    qualification_code: str


@dataclass(frozen=True)
class ExistingLeagueDraftIngestionResult:
    processed_league_count: int
    processed_draft_count: int
    qualified_draft_count: int
    failed_draft_ids: list[str]


def _extract_qualification_timestamps(
    raw_draft: dict[str, Any],
    details: dict[str, Any],
) -> tuple[datetime | None, datetime | None]:
    started_at = details.get("draft_started_at")
    completed_at = details.get("draft_completed_at")

    start_dt = (
        datetime.fromisoformat(started_at)
        if started_at
        else None
    )
    complete_dt = (
        datetime.fromisoformat(completed_at)
        if completed_at
        else None
    )

    return (
        start_dt.replace(tzinfo=None) if start_dt is not None else None,
        complete_dt.replace(tzinfo=None) if complete_dt is not None else None,
    )


async def ingest_draft(
    db: AsyncSession,
    sleeper: SleeperClient,
    *,
    league,
    draft,
) -> DraftIngestionResult:
    raw_draft = await sleeper.transport.get(
        f"draft/{draft.draft_id}"
    )
    raw_picks = await sleeper.read.get_draft_picks(
        draft.draft_id,
    )

    draft_row = transformers.draft_to_db(
        draft,
        return_dict=True,
    )
    await adp_crud.upsert_drafts(
        db,
        [draft_row],
    )

    player_ids = [
        str(raw_pick.get("player_id"))
        for raw_pick in raw_picks
        if isinstance(raw_pick, dict)
        and raw_pick.get("player_id") is not None
    ]
    players_by_id = await adp_crud.get_players_by_ids(
        db,
        player_ids,
    )

    selection_rows = [
        transformers.draft_selection_to_db(
            raw_pick=raw_pick,
            draft_id=draft.draft_id,
            league_id=league.league_id,
            season=str(draft.season),
            total_rosters=int(league.total_rosters),
            fallback_pick_no=index,
            return_dict=True,
        )
        for index, raw_pick in enumerate(raw_picks, start=1)
        if isinstance(raw_pick, dict)
    ]
    await adp_crud.replace_draft_selections(
        db,
        draft_id=draft.draft_id,
        selection_rows=selection_rows,
    )

    classification = classify_draft(
        raw_draft,
        raw_picks,
        league,
        players_by_id=players_by_id,
    )
    started_at, completed_at = _extract_qualification_timestamps(
        raw_draft,
        classification.qualification_details,
    )
    await adp_crud.upsert_draft_qualifications(
        db,
        [
            ADPDraftQualification(
                draft_id=draft.draft_id,
                league_id=league.league_id,
                draft_started_at=started_at,
                draft_completed_at=completed_at,
                draft_kind=classification.draft_kind,
                league_format=classification.league_format,
                qb_format=classification.qb_format,
                te_premium=classification.te_premium,
                scoring_format=classification.scoring_format,
                team_count=classification.team_count,
                round_count=classification.round_count,
                is_mock=classification.is_mock,
                is_complete=classification.is_complete,
                is_qualified=classification.is_qualified,
                qualification_code=classification.qualification_code,
                qualification_details=classification.qualification_details,
                classified_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ).model_dump()
        ],
    )

    return DraftIngestionResult(
        draft_id=draft.draft_id,
        league_id=league.league_id,
        pick_count=len(raw_picks),
        inserted_pick_count=len(selection_rows),
        is_qualified=classification.is_qualified,
        qualification_code=classification.qualification_code,
    )


async def ingest_draft_by_id(
    db: AsyncSession,
    sleeper: SleeperClient,
    *,
    draft_id: str,
) -> DraftIngestionResult:
    draft = await sleeper.read.get_draft(
        draft_id,
    )

    leagues_by_id = await adp_crud.get_leagues_by_ids(
        db,
        [draft.league_id],
    )
    league = leagues_by_id.get(
        draft.league_id,
    )

    if league is None:
        raw_league = await sleeper.read.get_league(
            draft.league_id,
        )
        await adp_crud.upsert_leagues(
            db,
            [
                transformers.league_to_db(
                    raw_league,
                    return_dict=True,
                )
            ],
        )
        league = League(
            **transformers.league_to_db(
                raw_league,
                return_dict=True,
            )
        )

    return await ingest_draft(
        db,
        sleeper,
        league=league,
        draft=draft,
    )


async def ingest_existing_league_drafts(
    db: AsyncSession,
    sleeper: SleeperClient,
    *,
    max_leagues: int | None = None,
) -> ExistingLeagueDraftIngestionResult:
    leagues = await adp_crud.get_existing_adp_seed_leagues(
        db,
        limit=max_leagues,
    )

    processed_draft_count = 0
    qualified_draft_count = 0
    failed_draft_ids: list[str] = []

    for league in leagues:
        try:
            drafts = await sleeper.read.get_drafts_league(
                league.league_id,
            )
        except Exception:
            logger.exception(
                "ADP draft discovery failed for league %s",
                league.league_id,
            )
            continue

        for draft in drafts:
            try:
                result = await ingest_draft(
                    db,
                    sleeper,
                    league=league,
                    draft=draft,
                )
                processed_draft_count += 1
                qualified_draft_count += int(result.is_qualified)
            except Exception:
                logger.exception(
                    "ADP draft ingestion failed for draft %s",
                    draft.draft_id,
                )
                failed_draft_ids.append(draft.draft_id)

    await db.commit()

    return ExistingLeagueDraftIngestionResult(
        processed_league_count=len(leagues),
        processed_draft_count=processed_draft_count,
        qualified_draft_count=qualified_draft_count,
        failed_draft_ids=failed_draft_ids,
    )


async def ingest_discovered_drafts(
    db: AsyncSession,
    sleeper: SleeperClient,
    *,
    max_drafts: int,
) -> list[DraftIngestionResult]:
    seeds = await adp_crud.get_ready_discovered_draft_ids(
        db,
        limit=max_drafts,
    )
    results: list[DraftIngestionResult] = []

    for seed in seeds:
        result = await ingest_draft_by_id(
            db,
            sleeper,
            draft_id=seed.draft_id,
        )
        results.append(result)

    await db.commit()
    return results
