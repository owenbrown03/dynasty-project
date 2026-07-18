from __future__ import annotations

import json
from datetime import UTC, datetime

from app.core.config import settings
from app.crud import adp as adp_crud
from app.schemas.adp import ADPFilters, ADPPlayerRow, ADPResponse, ADPSample


def _build_adp_cache_key(filters: ADPFilters) -> str:
    return "adp:" + json.dumps(
        filters.model_dump(mode="json"),
        sort_keys=True,
    )


async def get_adp(
    *,
    db,
    redis,
    filters: ADPFilters,
) -> ADPResponse:
    cache_key = _build_adp_cache_key(filters)

    if redis is not None:
        cached_payload = await redis.get(cache_key)
        if cached_payload:
            return ADPResponse.model_validate_json(
                cached_payload,
            )

    snapshot = await adp_crud.get_latest_adp_snapshot(
        db,
        season=filters.season,
        draft_kind=filters.draft_kind,
        qb_format=filters.qb_format,
        te_premium=filters.te_premium,
        team_count=filters.team_count,
        scoring_format=filters.scoring_format,
        start_date=filters.start_date,
        end_date=filters.end_date,
        minimum_draft_count=filters.minimum_draft_count,
        limit=filters.limit,
    )

    if snapshot is not None:
        sample_summary = snapshot.sample
        player_rows = snapshot.players
    else:
        sample_summary = await adp_crud.get_adp_sample_summary(
            db,
            season=filters.season,
            draft_kind=filters.draft_kind,
            qb_format=filters.qb_format,
            te_premium=filters.te_premium,
            team_count=filters.team_count,
            scoring_format=filters.scoring_format,
            start_date=filters.start_date,
            end_date=filters.end_date,
        )
        player_rows = await adp_crud.get_player_adp_aggregates(
            db,
            season=filters.season,
            draft_kind=filters.draft_kind,
            qb_format=filters.qb_format,
            te_premium=filters.te_premium,
            team_count=filters.team_count,
            scoring_format=filters.scoring_format,
            start_date=filters.start_date,
            end_date=filters.end_date,
            minimum_draft_count=filters.minimum_draft_count,
            limit=filters.limit,
        )

    response = ADPResponse(
        filters=filters,
        sample=ADPSample(
            draft_count=sample_summary.draft_count,
            pick_count=sample_summary.pick_count,
            earliest_draft_at=sample_summary.earliest_draft_at,
            latest_draft_at=sample_summary.latest_draft_at,
            generated_at=sample_summary.generated_at or datetime.now(UTC),
            data_source=sample_summary.data_source,
        ),
        players=[
            ADPPlayerRow(
                player_id=row.player_id,
                name=row.name,
                position=row.position,
                team=row.team,
                overall_adp=row.overall_adp,
                median_pick=row.median_pick,
                min_pick=row.min_pick,
                max_pick=row.max_pick,
                standard_deviation=row.standard_deviation,
                pick_count=row.pick_count,
                draft_count=row.draft_count,
                selection_rate=row.selection_rate,
            )
            for row in player_rows
        ],
    )

    if redis is not None:
        await redis.set(
            cache_key,
            response.model_dump_json(),
            ttl_seconds=settings.ADP_CACHE_TTL_SECONDS,
        )

    return response
