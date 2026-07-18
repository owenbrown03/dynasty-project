from datetime import datetime

from fastapi import APIRouter, Query

from app.api.deps import ContextDep
from app.core.config import settings
from app.schemas.adp import (
    ADPDatasetReport,
    ADPFilters,
    ADPMetadataResponse,
    ADPResponse,
)
from app.services.adp.report import build_adp_dataset_report, get_adp_metadata
from app.services.adp.service import get_adp


router = APIRouter()


@router.get(
    "",
    response_model=ADPResponse,
)
async def adp_endpoint(
    ctx: ContextDep,
    season: str | None = Query(default=None),
    draft_kind: str | None = Query(default=None),
    qb_format: str | None = Query(default=None),
    te_premium: str | None = Query(default=None),
    team_count: int | None = Query(default=None),
    scoring_format: str | None = Query(default=None),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    minimum_draft_count: int = Query(
        default=settings.ADP_MIN_PLAYER_DRAFT_COUNT,
        ge=1,
    ),
    limit: int = Query(default=300, ge=1, le=1000),
):
    return await get_adp(
        db=ctx.db,
        redis=ctx.redis,
        filters=ADPFilters(
            season=season,
            draft_kind=draft_kind,
            qb_format=qb_format,
            te_premium=te_premium,
            team_count=team_count,
            scoring_format=scoring_format,
            start_date=start_date,
            end_date=end_date,
            minimum_draft_count=minimum_draft_count,
            limit=limit,
        ),
    )


@router.get(
    "/metadata",
    response_model=ADPMetadataResponse,
)
async def adp_metadata_endpoint(
    ctx: ContextDep,
    season: str | None = Query(default=None),
    draft_kind: str | None = Query(default=None),
    qb_format: str | None = Query(default=None),
    te_premium: str | None = Query(default=None),
    team_count: int | None = Query(default=None),
    scoring_format: str | None = Query(default=None),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
):
    return await get_adp_metadata(
        ctx.db,
        filters=ADPFilters(
            season=season,
            draft_kind=draft_kind,
            qb_format=qb_format,
            te_premium=te_premium,
            team_count=team_count,
            scoring_format=scoring_format,
            start_date=start_date,
            end_date=end_date,
        ),
    )


@router.get(
    "/report",
    response_model=ADPDatasetReport,
)
async def adp_report_endpoint(
    ctx: ContextDep,
):
    return await build_adp_dataset_report(
        ctx.db,
    )
