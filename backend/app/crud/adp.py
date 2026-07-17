from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.base import _bulk_upsert
from app.models.db.adp import ADPDraftQualification
from app.models.db.sleeper.api import Draft, DraftSelection, League, Player


@dataclass(frozen=True)
class ADPPlayerAggregateRow:
    player_id: str
    name: str
    position: str | None
    team: str | None
    overall_adp: float
    median_pick: float
    min_pick: int
    max_pick: int
    standard_deviation: float | None
    pick_count: int
    draft_count: int
    selection_rate: float


@dataclass(frozen=True)
class ADPSampleSummary:
    draft_count: int
    pick_count: int
    earliest_draft_at: datetime | None
    latest_draft_at: datetime | None


async def get_existing_adp_seed_leagues(
    db: AsyncSession,
    *,
    limit: int | None = None,
) -> list[League]:
    statement = (
        select(League)
        .order_by(
            League.season.desc(),
            League.league_id.asc(),
        )
    )

    if limit is not None:
        statement = statement.limit(limit)

    result = await db.execute(statement)
    leagues = result.scalars().all()
    dynasty_leagues = [league for league in leagues if league.is_dynasty]

    if limit is not None:
        return dynasty_leagues[:limit]

    return dynasty_leagues


async def get_leagues_by_ids(
    db: AsyncSession,
    league_ids: Sequence[str],
) -> dict[str, League]:
    if not league_ids:
        return {}

    result = await db.execute(
        select(League).where(League.league_id.in_(list(league_ids)))
    )
    leagues = result.scalars().all()
    return {league.league_id: league for league in leagues}


async def get_players_by_ids(
    db: AsyncSession,
    player_ids: Sequence[str],
) -> dict[str, Player]:
    player_ids = [str(player_id) for player_id in player_ids if player_id]
    if not player_ids:
        return {}

    result = await db.execute(
        select(Player).where(Player.player_id.in_(player_ids))
    )
    players = result.scalars().all()
    return {player.player_id: player for player in players}


async def upsert_drafts(
    db: AsyncSession,
    draft_rows: list[dict],
) -> None:
    await _bulk_upsert(
        db,
        Draft,
        draft_rows,
        "draft_id",
    )


async def replace_draft_selections(
    db: AsyncSession,
    *,
    draft_id: str,
    selection_rows: list[dict],
) -> None:
    await db.execute(
        DraftSelection.__table__.delete().where(
            DraftSelection.draft_id == draft_id
        )
    )

    if selection_rows:
        await db.execute(
            insert(DraftSelection).values(selection_rows)
        )


async def upsert_draft_qualifications(
    db: AsyncSession,
    rows: list[dict],
) -> None:
    await _bulk_upsert(
        db,
        ADPDraftQualification,
        rows,
        "draft_id",
    )


def apply_adp_filters(
    statement,
    *,
    season: str | None = None,
    draft_kind: str | None = None,
    qb_format: str | None = None,
    te_premium: str | None = None,
    team_count: int | None = None,
    scoring_format: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
):
    conditions = [ADPDraftQualification.is_qualified.is_(True)]

    if season is not None:
        conditions.append(Draft.season == season)
    if draft_kind is not None:
        conditions.append(ADPDraftQualification.draft_kind == draft_kind)
    if qb_format is not None:
        conditions.append(ADPDraftQualification.qb_format == qb_format)
    if te_premium is not None:
        conditions.append(ADPDraftQualification.te_premium == te_premium)
    if team_count is not None:
        conditions.append(ADPDraftQualification.team_count == team_count)
    if scoring_format is not None:
        conditions.append(
            ADPDraftQualification.scoring_format == scoring_format
        )
    if start_date is not None:
        conditions.append(
            ADPDraftQualification.draft_completed_at >= start_date
        )
    if end_date is not None:
        conditions.append(
            ADPDraftQualification.draft_completed_at <= end_date
        )

    return statement.where(and_(*conditions))


async def get_adp_sample_summary(
    db: AsyncSession,
    *,
    season: str | None = None,
    draft_kind: str | None = None,
    qb_format: str | None = None,
    te_premium: str | None = None,
    team_count: int | None = None,
    scoring_format: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> ADPSampleSummary:
    statement = (
        select(
            func.count(func.distinct(ADPDraftQualification.draft_id)),
            func.count(DraftSelection.id),
            func.min(ADPDraftQualification.draft_completed_at),
            func.max(ADPDraftQualification.draft_completed_at),
        )
        .select_from(ADPDraftQualification)
        .join(Draft, Draft.draft_id == ADPDraftQualification.draft_id)
        .join(
            DraftSelection,
            DraftSelection.draft_id == ADPDraftQualification.draft_id,
        )
    )
    statement = apply_adp_filters(
        statement,
        season=season,
        draft_kind=draft_kind,
        qb_format=qb_format,
        te_premium=te_premium,
        team_count=team_count,
        scoring_format=scoring_format,
        start_date=start_date,
        end_date=end_date,
    )
    result = await db.execute(statement)
    draft_count, pick_count, earliest, latest = result.one()
    return ADPSampleSummary(
        draft_count=int(draft_count or 0),
        pick_count=int(pick_count or 0),
        earliest_draft_at=earliest,
        latest_draft_at=latest,
    )


async def get_player_adp_aggregates(
    db: AsyncSession,
    *,
    season: str | None = None,
    draft_kind: str | None = None,
    qb_format: str | None = None,
    te_premium: str | None = None,
    team_count: int | None = None,
    scoring_format: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    minimum_draft_count: int = 5,
    limit: int = 300,
) -> list[ADPPlayerAggregateRow]:
    sample_summary = await get_adp_sample_summary(
        db,
        season=season,
        draft_kind=draft_kind,
        qb_format=qb_format,
        te_premium=te_premium,
        team_count=team_count,
        scoring_format=scoring_format,
        start_date=start_date,
        end_date=end_date,
    )

    total_qualified_drafts = max(sample_summary.draft_count, 1)

    statement = (
        select(
            DraftSelection.player_id,
            func.concat(
                Player.first_name,
                " ",
                Player.last_name,
            ).label("name"),
            Player.position,
            Player.team,
            func.avg(DraftSelection.pick_no).label("overall_adp"),
            func.percentile_cont(0.5).within_group(
                DraftSelection.pick_no
            ).label("median_pick"),
            func.min(DraftSelection.pick_no).label("min_pick"),
            func.max(DraftSelection.pick_no).label("max_pick"),
            func.stddev_pop(DraftSelection.pick_no).label("stddev"),
            func.count(DraftSelection.id).label("pick_count"),
            func.count(func.distinct(DraftSelection.draft_id)).label("draft_count"),
        )
        .select_from(DraftSelection)
        .join(
            ADPDraftQualification,
            ADPDraftQualification.draft_id == DraftSelection.draft_id,
        )
        .join(Draft, Draft.draft_id == DraftSelection.draft_id)
        .join(Player, Player.player_id == DraftSelection.player_id)
        .where(DraftSelection.player_id.is_not(None))
        .group_by(
            DraftSelection.player_id,
            Player.first_name,
            Player.last_name,
            Player.position,
            Player.team,
        )
    )

    statement = apply_adp_filters(
        statement,
        season=season,
        draft_kind=draft_kind,
        qb_format=qb_format,
        te_premium=te_premium,
        team_count=team_count,
        scoring_format=scoring_format,
        start_date=start_date,
        end_date=end_date,
    ).having(
        func.count(func.distinct(DraftSelection.draft_id))
        >= minimum_draft_count
    ).order_by(
        func.avg(DraftSelection.pick_no).asc()
    ).limit(
        limit
    )

    result = await db.execute(statement)
    rows = result.all()

    return [
        ADPPlayerAggregateRow(
            player_id=str(player_id),
            name=str(name),
            position=position,
            team=team,
            overall_adp=float(overall_adp),
            median_pick=float(median_pick),
            min_pick=int(min_pick),
            max_pick=int(max_pick),
            standard_deviation=(
                float(stddev)
                if stddev is not None
                else None
            ),
            pick_count=int(pick_count),
            draft_count=int(draft_count),
            selection_rate=round(
                int(draft_count) / total_qualified_drafts,
                4,
            ),
        )
        for (
            player_id,
            name,
            position,
            team,
            overall_adp,
            median_pick,
            min_pick,
            max_pick,
            stddev,
            pick_count,
            draft_count,
        ) in rows
    ]
