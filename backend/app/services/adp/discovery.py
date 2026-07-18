from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import logging
import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud import adp as adp_crud
from app.integrations.sleeper.client import SleeperClient


logger = logging.getLogger(__name__)

DISCOVERY_NODE_USER = "user_id"
DISCOVERY_NODE_LEAGUE = "league_id"
DISCOVERY_NODE_DRAFT = "draft_id"


@dataclass(frozen=True)
class ADPDiscoveryBatchResult:
    claimed_node_count: int
    processed_node_count: int
    discovered_user_count: int
    discovered_league_count: int
    discovered_draft_count: int
    request_count: int
    stopped_reason: str | None


@dataclass
class DiscoveryBudgetState:
    request_count: int = 0
    discovered_user_count: int = 0
    discovered_league_count: int = 0
    discovered_draft_count: int = 0


def _utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _build_node_rows(
    *,
    node_type: str,
    values: list[str],
    source_type: str,
    source_value: str,
    discovery_depth: int,
) -> list[dict]:
    now = _utcnow_naive()
    return [
        {
            "node_type": node_type,
            "node_value": value,
            "source_type": source_type,
            "source_value": source_value,
            "discovery_depth": discovery_depth,
            "status": adp_crud.DISCOVERY_STATUS_PENDING,
            "attempt_count": 0,
            "created_at": now,
            "updated_at": now,
        }
        for value in values
    ]


def _remaining_budget(
    *,
    budget_limit: int,
    current_count: int,
) -> int:
    return max(budget_limit - current_count, 0)


async def seed_existing_leagues_for_adp_discovery(
    db: AsyncSession,
    *,
    limit: int | None = None,
) -> int:
    return await adp_crud.seed_existing_league_discovery_nodes(
        db,
        limit=limit,
    )


async def _handle_user_node(
    *,
    db: AsyncSession,
    sleeper: SleeperClient,
    node,
    budget: DiscoveryBudgetState,
) -> None:
    if node.discovery_depth >= settings.ADP_MAX_DISCOVERY_DEPTH:
        return

    pending_rows: list[dict] = []
    next_depth = node.discovery_depth + 1
    discovered_this_node = 0

    for season in settings.adp_crawl_seasons:
        if budget.request_count >= settings.ADP_MAX_REQUESTS_PER_RUN:
            break

        leagues = await sleeper.read.get_leagues(
            str(node.node_value),
            season,
        )
        budget.request_count += 1

        remaining_league_budget = _remaining_budget(
            budget_limit=settings.ADP_MAX_NEW_LEAGUES_PER_RUN,
            current_count=(
                budget.discovered_league_count
                + discovered_this_node
            ),
        )
        if remaining_league_budget <= 0:
            break

        league_ids = [
            league.league_id
            for league in leagues[:remaining_league_budget]
        ]
        discovered_this_node += len(league_ids)
        pending_rows.extend(
            _build_node_rows(
                node_type=DISCOVERY_NODE_LEAGUE,
                values=league_ids,
                source_type=DISCOVERY_NODE_USER,
                source_value=str(node.node_value),
                discovery_depth=next_depth,
            )
        )

    inserted = await adp_crud.enqueue_discovery_nodes(
        db,
        pending_rows,
    )
    budget.discovered_league_count += inserted


async def _handle_league_node(
    *,
    db: AsyncSession,
    sleeper: SleeperClient,
    node,
    budget: DiscoveryBudgetState,
) -> None:
    next_depth = node.discovery_depth + 1
    draft_rows: list[dict] = []
    user_rows: list[dict] = []

    if budget.request_count < settings.ADP_MAX_REQUESTS_PER_RUN:
        drafts = await sleeper.read.get_drafts_league(
            str(node.node_value),
        )
        budget.request_count += 1
        remaining_draft_budget = _remaining_budget(
            budget_limit=settings.ADP_MAX_NEW_DRAFTS_PER_RUN,
            current_count=budget.discovered_draft_count,
        )
        if remaining_draft_budget > 0:
            draft_rows = _build_node_rows(
                node_type=DISCOVERY_NODE_DRAFT,
                values=[
                    draft.draft_id
                    for draft in drafts[:remaining_draft_budget]
                ],
                source_type=DISCOVERY_NODE_LEAGUE,
                source_value=str(node.node_value),
                discovery_depth=next_depth,
            )

    if (
        node.discovery_depth < settings.ADP_MAX_DISCOVERY_DEPTH
        and budget.request_count < settings.ADP_MAX_REQUESTS_PER_RUN
    ):
        users = await sleeper.read.get_users(
            str(node.node_value),
        )
        budget.request_count += 1
        remaining_user_budget = _remaining_budget(
            budget_limit=settings.ADP_MAX_NEW_USERS_PER_RUN,
            current_count=budget.discovered_user_count,
        )
        if remaining_user_budget > 0:
            user_rows = _build_node_rows(
                node_type=DISCOVERY_NODE_USER,
                values=[
                    user.user_id
                    for user in users[:remaining_user_budget]
                ],
                source_type=DISCOVERY_NODE_LEAGUE,
                source_value=str(node.node_value),
                discovery_depth=next_depth,
            )

    inserted_drafts = await adp_crud.enqueue_discovery_nodes(
        db,
        draft_rows,
    )
    inserted_users = await adp_crud.enqueue_discovery_nodes(
        db,
        user_rows,
    )
    budget.discovered_draft_count += inserted_drafts
    budget.discovered_user_count += inserted_users


async def _handle_draft_node(
    *,
    node,
) -> None:
    del node
    return


async def process_adp_discovery_batch(
    db: AsyncSession,
    sleeper: SleeperClient,
    *,
    max_nodes: int | None = None,
    allow_when_disabled: bool = False,
) -> ADPDiscoveryBatchResult:
    if not settings.ADP_CRAWL_ENABLED and not allow_when_disabled:
        return ADPDiscoveryBatchResult(
            claimed_node_count=0,
            processed_node_count=0,
            discovered_user_count=0,
            discovered_league_count=0,
            discovered_draft_count=0,
            request_count=0,
            stopped_reason="crawl_disabled",
        )

    claimed_limit = min(
        max_nodes or settings.ADP_MAX_NODES_PER_RUN,
        settings.ADP_MAX_NODES_PER_RUN,
    )
    start_monotonic = time.monotonic()
    nodes = await adp_crud.claim_discovery_nodes(
        db,
        limit=claimed_limit,
        processing_timeout_seconds=settings.ADP_PROCESSING_TIMEOUT_SECONDS,
    )
    budget = DiscoveryBudgetState()
    processed_node_count = 0
    stopped_reason: str | None = None
    released_node_ids: list[str] = []

    for index, node in enumerate(nodes):
        elapsed_seconds = time.monotonic() - start_monotonic
        if elapsed_seconds >= settings.ADP_MAX_RUNTIME_SECONDS:
            stopped_reason = "runtime_budget_reached"
            released_node_ids = [
                remaining_node.id
                for remaining_node in nodes[index:]
            ]
            break
        if budget.request_count >= settings.ADP_MAX_REQUESTS_PER_RUN:
            stopped_reason = "request_budget_reached"
            released_node_ids = [
                remaining_node.id
                for remaining_node in nodes[index:]
            ]
            break

        try:
            if node.node_type == DISCOVERY_NODE_USER:
                await _handle_user_node(
                    db=db,
                    sleeper=sleeper,
                    node=node,
                    budget=budget,
                )
            elif node.node_type == DISCOVERY_NODE_LEAGUE:
                await _handle_league_node(
                    db=db,
                    sleeper=sleeper,
                    node=node,
                    budget=budget,
                )
            elif node.node_type == DISCOVERY_NODE_DRAFT:
                await _handle_draft_node(
                    node=node,
                )

            await adp_crud.mark_discovery_node_processed(
                db,
                node_id=node.id,
            )
            processed_node_count += 1
        except Exception as exc:
            logger.exception(
                "ADP discovery node failed: type=%s value=%s depth=%s",
                node.node_type,
                node.node_value,
                node.discovery_depth,
            )
            await adp_crud.mark_discovery_node_failed(
                db,
                node_id=node.id,
                failure_reason=str(exc),
                retry_delay_seconds=settings.ADP_PROCESSING_TIMEOUT_SECONDS,
            )

    if released_node_ids:
        await adp_crud.release_discovery_nodes(
            db,
            node_ids=released_node_ids,
        )

    await db.commit()

    return ADPDiscoveryBatchResult(
        claimed_node_count=len(nodes),
        processed_node_count=processed_node_count,
        discovered_user_count=budget.discovered_user_count,
        discovered_league_count=budget.discovered_league_count,
        discovered_draft_count=budget.discovered_draft_count,
        request_count=budget.request_count,
        stopped_reason=stopped_reason,
    )
