from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlmodel import select

from app.crud.base import _bulk_upsert
from app.models.db.adp import (
    ADPDraftQualification,
    ADPDiscoveryNode,
    ADPSnapshot,
    ADPSnapshotPlayer,
)
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
    generated_at: datetime | None = None
    data_source: str = "live"


@dataclass(frozen=True)
class ADPDistributionCount:
    key: str
    count: int


@dataclass(frozen=True)
class ADPDatasetReportRow:
    qualified_draft_count: int
    excluded_draft_count: int
    unique_league_count: int
    unique_root_source_count: int
    earliest_draft_at: datetime | None
    latest_draft_at: datetime | None


@dataclass(frozen=True)
class ADPDraftIngestionSeed:
    draft_id: str
    source_type: str | None
    source_value: str | None


@dataclass(frozen=True)
class ADPSnapshotResult:
    snapshot_id: str
    sample: ADPSampleSummary
    players: list[ADPPlayerAggregateRow]


@dataclass(frozen=True)
class ADPStoredDraftRequalificationRow:
    draft: Draft
    league: League
    qualification: ADPDraftQualification | None


DISCOVERY_STATUS_PENDING = "pending"
DISCOVERY_STATUS_PROCESSING = "processing"
DISCOVERY_STATUS_PROCESSED = "processed"
DISCOVERY_STATUS_FAILED = "failed"


def _dedupe_discovery_rows(
    rows: list[dict],
) -> list[dict]:
    deduped: dict[tuple[str, str], dict] = {}
    for row in rows:
        node_type = str(row["node_type"])
        node_value = str(row["node_value"])
        deduped[(node_type, node_value)] = {
            **row,
            "node_type": node_type,
            "node_value": node_value,
        }
    return list(deduped.values())


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


async def upsert_leagues(
    db: AsyncSession,
    league_rows: list[dict],
) -> None:
    await _bulk_upsert(
        db,
        League,
        league_rows,
        "league_id",
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


async def enqueue_discovery_nodes(
    db: AsyncSession,
    rows: list[dict],
) -> int:
    if not rows:
        return 0

    deduped = _dedupe_discovery_rows(rows)

    statement = (
        insert(ADPDiscoveryNode)
        .values(deduped)
        .on_conflict_do_nothing(
            index_elements=["node_type", "node_value"]
        )
        .returning(ADPDiscoveryNode.id)
    )
    result = await db.execute(statement)
    return len(result.all())


async def seed_existing_league_discovery_nodes(
    db: AsyncSession,
    *,
    limit: int | None = None,
) -> int:
    leagues = await get_existing_adp_seed_leagues(
        db,
        limit=limit,
    )
    inserted = await enqueue_discovery_nodes(
        db,
        [
            {
                "node_type": "league_id",
                "node_value": league.league_id,
                "source_type": "existing_db",
                "source_value": league.league_id,
                "discovery_depth": 0,
                "status": DISCOVERY_STATUS_PENDING,
                "attempt_count": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            for league in leagues
        ],
    )
    await db.commit()
    return inserted


async def reset_stale_processing_nodes(
    db: AsyncSession,
    *,
    processing_timeout_seconds: int,
    now: datetime | None = None,
) -> int:
    current = now or datetime.now(UTC)
    cutoff = current - timedelta(
        seconds=processing_timeout_seconds,
    )
    result = await db.execute(
        select(ADPDiscoveryNode).where(
            ADPDiscoveryNode.status == DISCOVERY_STATUS_PROCESSING,
            ADPDiscoveryNode.last_checked_at.is_not(None),
            ADPDiscoveryNode.last_checked_at
            < cutoff.replace(tzinfo=None),
        )
    )
    stale_nodes = result.scalars().all()

    for node in stale_nodes:
        node.status = DISCOVERY_STATUS_PENDING
        node.updated_at = current.replace(tzinfo=None)

    return len(stale_nodes)


async def claim_discovery_nodes(
    db: AsyncSession,
    *,
    limit: int,
    processing_timeout_seconds: int,
    now: datetime | None = None,
) -> list[ADPDiscoveryNode]:
    current = now or datetime.now(UTC)
    await reset_stale_processing_nodes(
        db,
        processing_timeout_seconds=processing_timeout_seconds,
        now=current,
    )

    statement = (
        select(ADPDiscoveryNode)
        .where(
            ADPDiscoveryNode.status.in_(
                [
                    DISCOVERY_STATUS_PENDING,
                    DISCOVERY_STATUS_FAILED,
                ]
            ),
            (
                ADPDiscoveryNode.next_retry_at.is_(None)
            )
            | (
                ADPDiscoveryNode.next_retry_at
                <= current.replace(tzinfo=None)
            ),
        )
        .order_by(
            ADPDiscoveryNode.discovery_depth.asc(),
            ADPDiscoveryNode.created_at.asc(),
        )
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    result = await db.execute(statement)
    nodes = result.scalars().all()

    for node in nodes:
        node.status = DISCOVERY_STATUS_PROCESSING
        node.attempt_count += 1
        node.last_checked_at = current.replace(tzinfo=None)
        node.updated_at = current.replace(tzinfo=None)

    await db.flush()
    return nodes


async def mark_discovery_node_processed(
    db: AsyncSession,
    *,
    node_id: str,
) -> None:
    result = await db.execute(
        select(ADPDiscoveryNode).where(
            ADPDiscoveryNode.id == node_id
        )
    )
    node = result.scalar_one()
    node.status = DISCOVERY_STATUS_PROCESSED
    node.failure_reason = None
    node.next_retry_at = None
    node.updated_at = datetime.utcnow()


async def mark_discovery_node_failed(
    db: AsyncSession,
    *,
    node_id: str,
    failure_reason: str,
    retry_delay_seconds: int,
) -> None:
    result = await db.execute(
        select(ADPDiscoveryNode).where(
            ADPDiscoveryNode.id == node_id
        )
    )
    node = result.scalar_one()
    node.status = DISCOVERY_STATUS_FAILED
    node.failure_reason = failure_reason
    node.next_retry_at = datetime.utcnow() + timedelta(
        seconds=retry_delay_seconds,
    )
    node.updated_at = datetime.utcnow()


async def release_discovery_nodes(
    db: AsyncSession,
    *,
    node_ids: Sequence[str],
) -> None:
    if not node_ids:
        return

    result = await db.execute(
        select(ADPDiscoveryNode).where(
            ADPDiscoveryNode.id.in_(list(node_ids))
        )
    )
    nodes = result.scalars().all()

    for node in nodes:
        node.status = DISCOVERY_STATUS_PENDING
        node.updated_at = datetime.utcnow()


async def get_ready_discovered_draft_ids(
    db: AsyncSession,
    *,
    limit: int,
) -> list[ADPDraftIngestionSeed]:
    qualification = aliased(ADPDraftQualification)
    result = await db.execute(
        select(
            ADPDiscoveryNode.node_value,
            ADPDiscoveryNode.source_type,
            ADPDiscoveryNode.source_value,
        )
        .select_from(ADPDiscoveryNode)
        .outerjoin(
            qualification,
            qualification.draft_id == ADPDiscoveryNode.node_value,
        )
        .where(
            ADPDiscoveryNode.node_type == "draft_id",
            ADPDiscoveryNode.status.in_(
                [
                    DISCOVERY_STATUS_PENDING,
                    DISCOVERY_STATUS_PROCESSED,
                ]
            ),
            qualification.draft_id.is_(None),
        )
        .order_by(
            ADPDiscoveryNode.updated_at.asc(),
            ADPDiscoveryNode.created_at.asc(),
        )
        .limit(limit)
    )
    return [
        ADPDraftIngestionSeed(
            draft_id=str(draft_id),
            source_type=source_type,
            source_value=source_value,
        )
        for draft_id, source_type, source_value in result.all()
    ]


async def get_discovery_status_counts(
    db: AsyncSession,
) -> list[ADPDistributionCount]:
    result = await db.execute(
        select(
            ADPDiscoveryNode.status,
            func.count(ADPDiscoveryNode.id),
        )
        .group_by(ADPDiscoveryNode.status)
        .order_by(ADPDiscoveryNode.status.asc())
    )
    return [
        ADPDistributionCount(
            key=str(key),
            count=int(count),
        )
        for key, count in result.all()
    ]


async def get_recent_discovery_nodes(
    db: AsyncSession,
    *,
    limit: int = 50,
) -> list[ADPDiscoveryNode]:
    result = await db.execute(
        select(ADPDiscoveryNode)
        .order_by(
            ADPDiscoveryNode.updated_at.desc(),
            ADPDiscoveryNode.created_at.desc(),
        )
        .limit(limit)
    )
    return result.scalars().all()


async def get_adp_dataset_report_row(
    db: AsyncSession,
) -> ADPDatasetReportRow:
    result = await db.execute(
        select(
            func.count(
                func.distinct(
                    ADPDraftQualification.draft_id,
                )
            ).filter(
                ADPDraftQualification.is_qualified.is_(True)
            ),
            func.count(
                func.distinct(
                    ADPDraftQualification.draft_id,
                )
            ).filter(
                ADPDraftQualification.is_qualified.is_(False)
            ),
            func.count(
                func.distinct(
                    ADPDraftQualification.league_id,
                )
            ),
            func.count(
                func.distinct(
                    func.concat(
                        func.coalesce(
                            ADPDiscoveryNode.source_type,
                            "",
                        ),
                        ":",
                        func.coalesce(
                            ADPDiscoveryNode.source_value,
                            "",
                        ),
                    )
                )
            ),
            func.min(ADPDraftQualification.draft_completed_at),
            func.max(ADPDraftQualification.draft_completed_at),
        )
        .select_from(ADPDraftQualification)
        .outerjoin(
            ADPDiscoveryNode,
            and_(
                ADPDiscoveryNode.node_type == "draft_id",
                ADPDiscoveryNode.node_value == ADPDraftQualification.draft_id,
            ),
        )
    )
    (
        qualified_draft_count,
        excluded_draft_count,
        unique_league_count,
        unique_root_source_count,
        earliest_draft_at,
        latest_draft_at,
    ) = result.one()
    return ADPDatasetReportRow(
        qualified_draft_count=int(qualified_draft_count or 0),
        excluded_draft_count=int(excluded_draft_count or 0),
        unique_league_count=int(unique_league_count or 0),
        unique_root_source_count=int(unique_root_source_count or 0),
        earliest_draft_at=earliest_draft_at,
        latest_draft_at=latest_draft_at,
    )


async def get_adp_distribution(
    db: AsyncSession,
    *,
    source: str,
) -> list[ADPDistributionCount]:
    if source == "qualification_code":
        key_column = ADPDraftQualification.qualification_code
        statement = (
            select(
                key_column,
                func.count(ADPDraftQualification.draft_id),
            )
            .group_by(key_column)
            .order_by(func.count(ADPDraftQualification.draft_id).desc(), key_column.asc())
        )
    elif source == "season":
        key_column = Draft.season
        statement = (
            select(
                key_column,
                func.count(ADPDraftQualification.draft_id),
            )
            .select_from(ADPDraftQualification)
            .join(Draft, Draft.draft_id == ADPDraftQualification.draft_id)
            .group_by(key_column)
            .order_by(func.count(ADPDraftQualification.draft_id).desc(), key_column.asc())
        )
    elif source == "draft_kind":
        key_column = ADPDraftQualification.draft_kind
        statement = (
            select(
                key_column,
                func.count(ADPDraftQualification.draft_id),
            )
            .group_by(key_column)
            .order_by(func.count(ADPDraftQualification.draft_id).desc(), key_column.asc())
        )
    elif source == "qb_format":
        key_column = ADPDraftQualification.qb_format
        statement = (
            select(
                key_column,
                func.count(ADPDraftQualification.draft_id),
            )
            .group_by(key_column)
            .order_by(func.count(ADPDraftQualification.draft_id).desc(), key_column.asc())
        )
    elif source == "te_premium":
        key_column = ADPDraftQualification.te_premium
        statement = (
            select(
                key_column,
                func.count(ADPDraftQualification.draft_id),
            )
            .group_by(key_column)
            .order_by(func.count(ADPDraftQualification.draft_id).desc(), key_column.asc())
        )
    elif source == "scoring_format":
        key_column = ADPDraftQualification.scoring_format
        statement = (
            select(
                key_column,
                func.count(ADPDraftQualification.draft_id),
            )
            .group_by(key_column)
            .order_by(func.count(ADPDraftQualification.draft_id).desc(), key_column.asc())
        )
    elif source == "team_count":
        key_column = ADPDraftQualification.team_count
        statement = (
            select(
                key_column,
                func.count(ADPDraftQualification.draft_id),
            )
            .group_by(key_column)
            .order_by(func.count(ADPDraftQualification.draft_id).desc(), key_column.asc())
        )
    elif source == "discovery_source":
        key_column = ADPDiscoveryNode.source_type
        statement = (
            select(
                key_column,
                func.count(ADPDiscoveryNode.id),
            )
            .group_by(key_column)
            .order_by(func.count(ADPDiscoveryNode.id).desc(), key_column.asc())
        )
    elif source == "discovery_depth":
        key_column = ADPDiscoveryNode.discovery_depth
        statement = (
            select(
                key_column,
                func.count(ADPDiscoveryNode.id),
            )
            .group_by(key_column)
            .order_by(key_column.asc())
        )
    elif source == "discovery_status":
        key_column = ADPDiscoveryNode.status
        statement = (
            select(
                key_column,
                func.count(ADPDiscoveryNode.id),
            )
            .group_by(key_column)
            .order_by(key_column.asc())
        )
    else:
        raise ValueError(f"Unsupported ADP distribution source: {source}")

    result = await db.execute(statement)
    return [
        ADPDistributionCount(
            key=str(key if key is not None else "unknown"),
            count=int(count),
        )
        for key, count in result.all()
    ]


async def get_filtered_adp_distribution(
    db: AsyncSession,
    *,
    source: str,
    season: str | None = None,
    draft_kind: str | None = None,
    qb_format: str | None = None,
    te_premium: str | None = None,
    team_count: int | None = None,
    scoring_format: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[ADPDistributionCount]:
    if source == "season":
        key_column = Draft.season
    elif source == "draft_kind":
        key_column = ADPDraftQualification.draft_kind
    elif source == "qb_format":
        key_column = ADPDraftQualification.qb_format
    elif source == "te_premium":
        key_column = ADPDraftQualification.te_premium
    elif source == "team_count":
        key_column = ADPDraftQualification.team_count
    elif source == "scoring_format":
        key_column = ADPDraftQualification.scoring_format
    else:
        raise ValueError(f"Unsupported filtered ADP distribution source: {source}")

    statement = (
        select(
            key_column,
            func.count(ADPDraftQualification.draft_id),
        )
        .select_from(ADPDraftQualification)
        .join(Draft, Draft.draft_id == ADPDraftQualification.draft_id)
        .group_by(key_column)
        .order_by(
            func.count(ADPDraftQualification.draft_id).desc(),
            key_column.asc(),
        )
    )
    statement = apply_adp_filters(
        statement,
        season=None if source == "season" else season,
        draft_kind=None if source == "draft_kind" else draft_kind,
        qb_format=None if source == "qb_format" else qb_format,
        te_premium=None if source == "te_premium" else te_premium,
        team_count=None if source == "team_count" else team_count,
        scoring_format=None if source == "scoring_format" else scoring_format,
        start_date=start_date,
        end_date=end_date,
    )

    result = await db.execute(statement)
    return [
        ADPDistributionCount(
            key=str(key if key is not None else "unknown"),
            count=int(count),
        )
        for key, count in result.all()
    ]


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


async def get_stored_drafts_for_requalification(
    db: AsyncSession,
    *,
    limit: int,
    offset: int = 0,
    season: str | None = None,
) -> list[ADPStoredDraftRequalificationRow]:
    statement = (
        select(
            Draft,
            League,
            ADPDraftQualification,
        )
        .select_from(Draft)
        .join(League, League.league_id == Draft.league_id)
        .outerjoin(
            ADPDraftQualification,
            ADPDraftQualification.draft_id == Draft.draft_id,
        )
        .order_by(
            Draft.season.desc(),
            Draft.draft_id.asc(),
        )
        .offset(offset)
        .limit(limit)
    )

    if season is not None:
        statement = statement.where(Draft.season == season)

    result = await db.execute(statement)
    return [
        ADPStoredDraftRequalificationRow(
            draft=draft,
            league=league,
            qualification=qualification,
        )
        for draft, league, qualification in result.all()
    ]


async def get_draft_selections_by_draft_ids(
    db: AsyncSession,
    draft_ids: Sequence[str],
) -> dict[str, list[DraftSelection]]:
    if not draft_ids:
        return {}

    result = await db.execute(
        select(DraftSelection)
        .where(DraftSelection.draft_id.in_(list(draft_ids)))
        .order_by(
            DraftSelection.draft_id.asc(),
            DraftSelection.pick_no.asc(),
        )
    )
    grouped: dict[str, list[DraftSelection]] = {}
    for selection in result.scalars().all():
        grouped.setdefault(
            selection.draft_id,
            [],
        ).append(selection)
    return grouped


def _apply_snapshot_filters(
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
    minimum_draft_count: int = 5,
    calculation_version: str = "v1",
):
    conditions = [
        ADPSnapshot.calculation_version == calculation_version,
        ADPSnapshot.minimum_draft_count == minimum_draft_count,
    ]

    if season is None:
        conditions.append(ADPSnapshot.season.is_(None))
    else:
        conditions.append(ADPSnapshot.season == season)

    if draft_kind is None:
        conditions.append(ADPSnapshot.draft_kind.is_(None))
    else:
        conditions.append(ADPSnapshot.draft_kind == draft_kind)

    if qb_format is None:
        conditions.append(ADPSnapshot.qb_format.is_(None))
    else:
        conditions.append(ADPSnapshot.qb_format == qb_format)

    if te_premium is None:
        conditions.append(ADPSnapshot.te_premium.is_(None))
    else:
        conditions.append(ADPSnapshot.te_premium == te_premium)

    if team_count is None:
        conditions.append(ADPSnapshot.team_count.is_(None))
    else:
        conditions.append(ADPSnapshot.team_count == team_count)

    if scoring_format is None:
        conditions.append(ADPSnapshot.scoring_format.is_(None))
    else:
        conditions.append(ADPSnapshot.scoring_format == scoring_format)

    if start_date is None:
        conditions.append(ADPSnapshot.start_date.is_(None))
    else:
        conditions.append(
            ADPSnapshot.start_date
            == start_date.replace(tzinfo=None)
        )

    if end_date is None:
        conditions.append(ADPSnapshot.end_date.is_(None))
    else:
        conditions.append(
            ADPSnapshot.end_date
            == end_date.replace(tzinfo=None)
        )

    return statement.where(and_(*conditions))


async def get_latest_adp_snapshot(
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
    calculation_version: str = "v1",
    limit: int = 300,
) -> ADPSnapshotResult | None:
    statement = select(ADPSnapshot)
    statement = _apply_snapshot_filters(
        statement,
        season=season,
        draft_kind=draft_kind,
        qb_format=qb_format,
        te_premium=te_premium,
        team_count=team_count,
        scoring_format=scoring_format,
        start_date=start_date,
        end_date=end_date,
        minimum_draft_count=minimum_draft_count,
        calculation_version=calculation_version,
    ).order_by(
        ADPSnapshot.generated_at.desc(),
        ADPSnapshot.id.desc(),
    ).limit(1)
    result = await db.execute(statement)
    snapshot = result.scalar_one_or_none()

    if snapshot is None:
        return None

    player_result = await db.execute(
        select(ADPSnapshotPlayer)
        .where(ADPSnapshotPlayer.snapshot_id == snapshot.id)
        .order_by(ADPSnapshotPlayer.rank.asc())
        .limit(limit)
    )
    players = player_result.scalars().all()

    return ADPSnapshotResult(
        snapshot_id=snapshot.id,
        sample=ADPSampleSummary(
            draft_count=snapshot.draft_count,
            pick_count=snapshot.pick_count,
            earliest_draft_at=snapshot.earliest_draft_at,
            latest_draft_at=snapshot.latest_draft_at,
            generated_at=snapshot.generated_at.replace(tzinfo=UTC),
            data_source="snapshot",
        ),
        players=[
            ADPPlayerAggregateRow(
                player_id=player.player_id,
                name=player.name,
                position=player.position,
                team=player.team,
                overall_adp=player.overall_adp,
                median_pick=player.median_pick,
                min_pick=player.min_pick,
                max_pick=player.max_pick,
                standard_deviation=player.standard_deviation,
                pick_count=player.pick_count,
                draft_count=player.draft_count,
                selection_rate=player.selection_rate,
            )
            for player in players
        ],
    )


async def create_adp_snapshot(
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
    calculation_version: str = "v1",
    row_limit: int = 5000,
    skip_empty: bool = False,
) -> ADPSnapshotResult | None:
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

    if skip_empty and sample_summary.draft_count == 0:
        return None

    player_rows = await get_player_adp_aggregates(
        db,
        season=season,
        draft_kind=draft_kind,
        qb_format=qb_format,
        te_premium=te_premium,
        team_count=team_count,
        scoring_format=scoring_format,
        start_date=start_date,
        end_date=end_date,
        minimum_draft_count=minimum_draft_count,
        limit=row_limit,
    )

    current = datetime.now(UTC).replace(tzinfo=None)
    snapshot = ADPSnapshot(
        calculation_version=calculation_version,
        season=season,
        draft_kind=draft_kind,
        qb_format=qb_format,
        te_premium=te_premium,
        team_count=team_count,
        scoring_format=scoring_format,
        start_date=start_date.replace(tzinfo=None) if start_date else None,
        end_date=end_date.replace(tzinfo=None) if end_date else None,
        minimum_draft_count=minimum_draft_count,
        draft_count=sample_summary.draft_count,
        pick_count=sample_summary.pick_count,
        earliest_draft_at=sample_summary.earliest_draft_at,
        latest_draft_at=sample_summary.latest_draft_at,
        generated_at=current,
        created_at=current,
        updated_at=current,
    )
    db.add(snapshot)
    await db.flush()

    snapshot_players = [
        ADPSnapshotPlayer(
            snapshot_id=snapshot.id,
            player_id=row.player_id,
            rank=index,
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
            created_at=current,
        )
        for index, row in enumerate(player_rows, start=1)
    ]
    if snapshot_players:
        db.add_all(snapshot_players)
    await db.flush()

    return ADPSnapshotResult(
        snapshot_id=snapshot.id,
        sample=ADPSampleSummary(
            draft_count=sample_summary.draft_count,
            pick_count=sample_summary.pick_count,
            earliest_draft_at=sample_summary.earliest_draft_at,
            latest_draft_at=sample_summary.latest_draft_at,
            generated_at=snapshot.generated_at.replace(tzinfo=UTC),
            data_source="snapshot",
        ),
        players=player_rows,
    )
