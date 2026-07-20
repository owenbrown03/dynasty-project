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


@dataclass(frozen=True)
class StoredDraftRequalificationResult:
    processed_draft_count: int
    qualified_draft_count: int
    reclassified_count: int
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


async def _persist_classification(
    db: AsyncSession,
    *,
    draft_id: str,
    league_id: str,
    raw_draft: dict[str, Any],
    classification,
) -> None:
    started_at, completed_at = _extract_qualification_timestamps(
        raw_draft,
        classification.qualification_details,
    )
    await adp_crud.upsert_draft_qualifications(
        db,
        [
            ADPDraftQualification(
                draft_id=draft_id,
                league_id=league_id,
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


def _build_stored_draft_payload(
    *,
    draft,
    league,
    qualification: ADPDraftQualification | None,
    picks: list[dict[str, Any]],
) -> dict[str, Any]:
    max_round = max(
        (
            pick.get("round")
            for pick in picks
            if pick.get("round") is not None
        ),
        default=None,
    )
    payload: dict[str, Any] = {
        "draft_id": draft.draft_id,
        "league_id": draft.league_id,
        "season": draft.season,
        "draft_order": draft.draft_order or {},
        "slot_to_roster_id": draft.slot_to_roster_id or {},
        "settings": {
            "rounds": (
                qualification.round_count
                if qualification and qualification.round_count is not None
                else max_round
                or league.settings.get("draft_rounds")
            ),
        },
        "metadata": {},
    }
    if qualification is not None:
        if qualification.draft_started_at is not None:
            payload["start_time"] = int(
                qualification.draft_started_at.timestamp() * 1000
            )
        if qualification.draft_completed_at is not None:
            completed_ms = int(
                qualification.draft_completed_at.timestamp() * 1000
            )
            payload["completed_at"] = completed_ms
            payload["last_picked"] = completed_ms
        if qualification.league_format == "keeper":
            payload["settings"]["is_keeper"] = True
        if qualification.qualification_code == "auction":
            payload["settings"]["type"] = "auction"
        if qualification.qualification_code == "mock":
            payload["status"] = "mock_draft_complete"
    return payload


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
    await _persist_classification(
        db,
        draft_id=draft.draft_id,
        league_id=league.league_id,
        raw_draft=raw_draft,
        classification=classification,
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


async def requalify_stored_drafts(
    db: AsyncSession,
    *,
    limit: int,
    offset: int = 0,
    season: str | None = None,
) -> StoredDraftRequalificationResult:
    rows = await adp_crud.get_stored_drafts_for_requalification(
        db,
        limit=limit,
        offset=offset,
        season=season,
    )
    selections_by_draft_id = await adp_crud.get_draft_selections_by_draft_ids(
        db,
        [row.draft.draft_id for row in rows],
    )
    player_ids = [
        selection.player_id
        for selections in selections_by_draft_id.values()
        for selection in selections
        if selection.player_id
    ]
    players_by_id = await adp_crud.get_players_by_ids(
        db,
        player_ids,
    )

    processed_draft_count = 0
    qualified_draft_count = 0
    reclassified_count = 0
    failed_draft_ids: list[str] = []

    for row in rows:
        try:
            selection_rows = selections_by_draft_id.get(
                row.draft.draft_id,
                [],
            )
            raw_picks = [
                {
                    "round": selection.round,
                    "pick_no": selection.pick_no,
                    "round_slot": selection.round_slot,
                    "roster_id": selection.roster_id,
                    "player_id": selection.player_id,
                    "is_keeper": selection.is_keeper,
                }
                for selection in selection_rows
            ]
            raw_draft = _build_stored_draft_payload(
                draft=row.draft,
                league=row.league,
                qualification=row.qualification,
                picks=raw_picks,
            )
            classification = classify_draft(
                raw_draft,
                raw_picks,
                row.league,
                players_by_id=players_by_id,
            )
            previous_code = (
                row.qualification.qualification_code
                if row.qualification is not None
                else None
            )
            await _persist_classification(
                db,
                draft_id=row.draft.draft_id,
                league_id=row.league.league_id,
                raw_draft=raw_draft,
                classification=classification,
            )
            processed_draft_count += 1
            qualified_draft_count += int(classification.is_qualified)
            reclassified_count += int(
                previous_code != classification.qualification_code
            )
        except Exception:
            logger.exception(
                "ADP draft requalification failed for draft %s",
                row.draft.draft_id,
            )
            failed_draft_ids.append(row.draft.draft_id)

    await db.commit()
    return StoredDraftRequalificationResult(
        processed_draft_count=processed_draft_count,
        qualified_draft_count=qualified_draft_count,
        reclassified_count=reclassified_count,
        failed_draft_ids=failed_draft_ids,
    )
