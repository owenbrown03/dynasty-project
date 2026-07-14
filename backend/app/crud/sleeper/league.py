import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Literal, List, Set

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.models.db.sleeper import api as model
from app.services.sleeper import transformers
from app.crud.base import _bulk_upsert
from app.crud.sleeper.personal import upsert_league_sort_orders
from app.core.concurrency import bounded_gather

logger = logging.getLogger(__name__)

FETCH_CHUNK_SIZE = 250
DB_BATCH_SIZE = 100
FULL_REFRESH_INTERVAL_DAYS = 7


# --------------------------------------------------
# Queries
# --------------------------------------------------

async def get_league_map(db: AsyncSession) -> dict[str, str]:
    result = await db.execute(
        select(model.League.league_id, model.League.name)
    )
    return {league_id: name for league_id, name in result.all()}


async def get_existing_leagues(db: AsyncSession, league_ids: List[str]) -> Set[str]:
    result = await db.execute(
        select(model.League.league_id).where(
            model.League.league_id.in_(league_ids)
        )
    )
    return set(result.scalars().all())


async def get_incomplete_league_ids(
    db: AsyncSession,
    league_ids: List[str],
) -> Set[str]:
    result = await db.execute(
        select(
            model.League.league_id,
            model.League.settings,
            model.League.scoring_settings,
            model.League.roster_positions,
        ).where(
            model.League.league_id.in_(league_ids)
        )
    )

    incomplete_ids: set[str] = set()

    for league_id, settings, scoring_settings, roster_positions in result.all():
        if not settings or not scoring_settings or not roster_positions:
            incomplete_ids.add(league_id)

    return incomplete_ids


async def get_sync_states(
    db: AsyncSession,
    league_ids: List[str],
) -> dict[str, model.LeagueSyncState]:
    """
    Returns {league_id: LeagueSyncState} for known synced leagues.

    last_synced_week:
        Used to find transaction weeks we have never fetched.

    last_synced_at:
        Used to decide whether today's roster / FAAB / taxi / IR
        data has already been refreshed.
    """

    result = await db.execute(
        select(
            model.LeagueSyncState,
        ).where(
            model.LeagueSyncState.league_id.in_(
                league_ids,
            )
        )
    )

    sync_states = result.scalars().all()

    return {
        sync_state.league_id: sync_state
        for sync_state in sync_states
    }


async def get_playoff_matchups_by_league_ids(
    db: AsyncSession,
    league_ids: List[str],
) -> dict[str, list[model.PlayoffMatchup]]:
    if not league_ids:
        return {}

    result = await db.execute(
        select(
            model.PlayoffMatchup,
        ).where(
            model.PlayoffMatchup.league_id.in_(
                league_ids,
            )
        )
    )

    rows = result.scalars().all()
    by_league_id: dict[str, list[model.PlayoffMatchup]] = {}

    for row in rows:
        by_league_id.setdefault(
            row.league_id,
            [],
        ).append(
            row,
        )

    return by_league_id


def was_synced_today(
    sync_state: model.LeagueSyncState | None,
) -> bool:
    """
    Treat a league as fresh only when we successfully synced it
    at least once during the current UTC calendar day.
    """

    if sync_state is None:
        return False

    if sync_state.last_synced_at is None:
        return False

    return (
        sync_state.last_synced_at.date()
        == datetime.now(UTC).date()
    )


def needs_full_refresh(
    sync_state: model.LeagueSyncState | None,
) -> bool:
    if sync_state is None:
        return True

    if sync_state.last_full_synced_at is None:
        return True

    refresh_cutoff = datetime.now() - timedelta(
        days=FULL_REFRESH_INTERVAL_DAYS,
    )

    return sync_state.last_full_synced_at < refresh_cutoff


def get_transaction_weeks_to_fetch(
    *,
    last_synced_week: int,
    curr_week: int,
) -> list[int]:
    """
    Always re-fetch the current week because trades and waiver activity
    can happen multiple times during the same NFL week.

    Also backfill any earlier weeks we have not seen yet.
    """

    first_missing_week = max(
        last_synced_week + 1,
        1,
    )

    missing_weeks = list(
        range(
            first_missing_week,
            curr_week + 1,
        )
    )

    if curr_week not in missing_weeks:
        missing_weeks.append(
            curr_week,
        )

    return sorted(
        set(missing_weeks),
    )

# --------------------------------------------------
# Core sync entry point
# --------------------------------------------------

async def sync_leagues(
    db: AsyncSession,
    raw_leagues,
    curr_week: int,
    sleeper,
    *,
    force: bool = False,
    existing_refresh: Literal[
        "full",
        "transactions_only",
    ] = "full",
    user_id: str | None = None,
):
    curr_week = max(curr_week, 1)

    sleeper_order = [
        l.league_id
        for l in raw_leagues
        if l and l.league_id
    ]

    leagues = list(
        {l.league_id: l for l in raw_leagues if l and l.league_id}.values()
    )

    if not leagues:
        return {"status": "skipped", "synced_count": 0}

    logger.info(
        "Starting ingestion for %s leagues force=%s",
        len(leagues),
        force,
    )

    all_league_ids = [l.league_id for l in leagues]

    # AsyncSession does not support concurrent DB operations.
    existing_ids = await get_existing_leagues(
        db,
        all_league_ids,
    )
    sync_states = await get_sync_states(
        db,
        all_league_ids,
    )
    incomplete_league_ids = await get_incomplete_league_ids(
        db,
        all_league_ids,
    )

    success_count = 0
    failed_batches = 0
    fetched_bundle_count = 0

    total_leagues = len(
        leagues,
    )

    for chunk_start in range(
        0,
        total_leagues,
        FETCH_CHUNK_SIZE,
    ):
        league_chunk = leagues[
            chunk_start:chunk_start + FETCH_CHUNK_SIZE
        ]
        bundles = await bounded_gather(
            [
                fetch_league_bundle(
                    league=league,
                    curr_week=curr_week,
                    sleeper=sleeper,
                    existing_ids=existing_ids,
                    sync_states=sync_states,
                    incomplete_league_ids=incomplete_league_ids,
                    force=force,
                    existing_refresh=existing_refresh,
                )
                for league in league_chunk
            ],
            log_every=len(league_chunk),
            progress_total=total_leagues,
            progress_offset=chunk_start,
            progress_label="leagues",
        )

        bundles = [
            bundle
            for bundle in bundles
            if isinstance(bundle, dict)
        ]

        if not bundles:
            logger.info(
                "[SYNC] progress=%s/%s persisted=%s failed_batches=%s",
                min(
                    chunk_start + len(league_chunk),
                    total_leagues,
                ),
                total_leagues,
                success_count,
                failed_batches,
            )
            continue

        chunk_success_count, chunk_failed_batches = await _save_bundles(
            db=db,
            bundles=bundles,
        )

        success_count += chunk_success_count
        failed_batches += chunk_failed_batches
        fetched_bundle_count += len(bundles)

        logger.info(
            "[SYNC] progress=%s/%s persisted=%s (+%s) failed_batches=%s",
            min(
                chunk_start + len(league_chunk),
                total_leagues,
            ),
            total_leagues,
            success_count,
            chunk_success_count,
            failed_batches,
        )

        sync_session = getattr(
            db,
            "sync_session",
            None,
        )
        if sync_session is not None:
            sync_session.expunge_all()

    if fetched_bundle_count == 0:
        return {
            "status": "skipped",
            "synced_count": 0,
            "reason": "no_new_data",
        }

    if user_id and sleeper_order:
        await upsert_league_sort_orders(
            db=db,
            user_id=user_id,
            league_ids_in_order=sleeper_order,
        )

    return {
        "status": "completed",
        "synced_count": success_count,
        "failed_batches": failed_batches,
    }


# --------------------------------------------------
# Bundle fetching
# --------------------------------------------------

async def fetch_league_bundle(
    *,
    league,
    curr_week: int,
    sleeper,
    existing_ids: Set[str],
    sync_states: dict[str, model.LeagueSyncState],
    incomplete_league_ids: Set[str],
    force: bool = False,
    existing_refresh: Literal[
        "full",
        "transactions_only",
    ] = "full",
):
    """
    Daily full roster refresh plus transaction backfill.

    Normal behavior:
    - Skip a league if it was already fully refreshed today.
    - Refresh league, users, rosters, and current-week transactions
      once per day.

    Force behavior:
    - Refresh immediately even if already synced today.
    """

    league_id = league.league_id

    if not league_id:
        return None

    is_new = league_id not in existing_ids

    sync_state = sync_states.get(
        league_id,
    )

    last_synced_week = (
        sync_state.last_synced_week
        if sync_state is not None
        else 0
    )

    full_refresh_due = (
        is_new
        or force
        or league_id in incomplete_league_ids
        or needs_full_refresh(sync_state)
    )

    needs_refresh = (
        full_refresh_due
        or not was_synced_today(sync_state)
    )

    should_fetch_brackets = (
        getattr(
            league,
            "status",
            None,
        )
        == "complete"
    )

    if not needs_refresh and not should_fetch_brackets:
        return None

    transaction_weeks = get_transaction_weeks_to_fetch(
        last_synced_week=last_synced_week,
        curr_week=curr_week,
    )

    try:
        if (
            not is_new
            and existing_refresh
            == "transactions_only"
            and not full_refresh_due
        ):
            tx_lists, winners_bracket, losers_bracket, traded_picks = await asyncio.gather(
                asyncio.gather(
                    *[
                        sleeper.read.get_transactions(
                            league_id,
                            week,
                        )
                        for week in transaction_weeks
                    ],
                    return_exceptions=True,
                ),
                sleeper.read.get_winners_bracket(
                    league_id,
                )
                if should_fetch_brackets
                else asyncio.sleep(
                    0,
                    result=[],
                ),
                sleeper.read.get_losers_bracket(
                    league_id,
                )
                if should_fetch_brackets
                else asyncio.sleep(
                    0,
                    result=[],
                ),
                sleeper.read.get_traded_picks(
                    league_id,
                ),
            )

            transactions = [
                transaction
                for batch in tx_lists
                if isinstance(batch, list)
                for transaction in batch
            ]

            bundle = {
                "league_id": league_id,
                "transactions": transactions,
                "traded_picks": traded_picks if isinstance(traded_picks, list) else [],
                "transactions_only": True,
                "synced_week": max(
                    last_synced_week,
                    curr_week,
                ),
            }

            if should_fetch_brackets:
                bundle["winners_bracket"] = winners_bracket
                bundle["losers_bracket"] = losers_bracket

            return bundle

        (
            league_obj,
            users,
            rosters,
            drafts,
            tx_lists,
            winners_bracket,
            losers_bracket,
            traded_picks,
        ) = await asyncio.gather(
            sleeper.read.get_league(
                league_id,
            ),
            sleeper.read.get_users(
                league_id,
            ),
            sleeper.read.get_rosters(
                league_id,
            ),
            sleeper.read.get_drafts_league(
                league_id,
            ),
            asyncio.gather(
                *[
                    sleeper.read.get_transactions(
                        league_id,
                        week,
                    )
                    for week in transaction_weeks
                ],
                return_exceptions=True,
            ),
            sleeper.read.get_winners_bracket(
                league_id,
            )
            if should_fetch_brackets
            else asyncio.sleep(
                0,
                result=[],
            ),
            sleeper.read.get_losers_bracket(
                league_id,
            )
            if should_fetch_brackets
            else asyncio.sleep(
                0,
                result=[],
            ),
            sleeper.read.get_traded_picks(
                league_id,
            ),
        )

        draft_pick_lists = (
            await asyncio.gather(
                *[
                    sleeper.read.get_draft_picks(
                        draft.draft_id,
                    )
                    for draft in drafts
                ],
                return_exceptions=True,
            )
            if drafts
            else []
        )

        transactions = [
            transaction
            for batch in tx_lists
            if isinstance(batch, list)
            for transaction in batch
        ]

        draft_picks_by_draft_id = {
            draft.draft_id: (
                draft_pick_list
                if isinstance(draft_pick_list, list)
                else []
            )
            for draft, draft_pick_list in zip(
                drafts,
                draft_pick_lists,
                strict=False,
            )
        }

        return {
            "league_id": league_id,

            # Daily refresh now includes the current league / users / rosters.
            "league": league_obj,
            "users": users,
            "rosters": rosters,
            "drafts": drafts,
            "draft_picks_by_draft_id": draft_picks_by_draft_id,

            "transactions": transactions,
            "traded_picks": traded_picks if isinstance(traded_picks, list) else [],
            "winners_bracket": winners_bracket,
            "losers_bracket": losers_bracket,

            # Keep this false so save_league_bundle_to_db()
            # upserts the latest roster state.
            "transactions_only": False,

            # Used for sync-state update after successful save.
            "synced_week": max(
                last_synced_week,
                curr_week,
            ),
        }

    except Exception as error:
        logger.error(
            "[BUNDLE ERROR] league=%s err=%s",
            league_id,
            error,
            exc_info=True,
        )
        return None


def _chunked(
    items: list,
    chunk_size: int,
):
    for start in range(
        0,
        len(items),
        chunk_size,
    ):
        yield items[
            start:start + chunk_size
        ]


async def _save_bundles(
    *,
    db: AsyncSession,
    bundles: list[dict],
) -> tuple[int, int]:
    success_count = 0
    failed_batches = 0
    synced_bundles: list[dict] = []

    for bundle_chunk in _chunked(
        bundles,
        DB_BATCH_SIZE,
    ):
        try:
            async with db.begin_nested():
                for bundle in bundle_chunk:
                    ok = await save_league_bundle_to_db(
                        db,
                        bundle,
                        commit=False,
                    )

                    if not ok:
                        raise RuntimeError(
                            "bundle save failed",
                        )

                await db.flush()

            success_count += len(
                bundle_chunk,
            )
            synced_bundles.extend(
                bundle_chunk,
            )

        except Exception as error:
            failed_batches += 1
            logger.error(
                "[DB BATCH ERROR] %s",
                error,
                exc_info=True,
            )

    if synced_bundles:
        await _update_sync_states(
            db=db,
            bundles=synced_bundles,
        )

    await db.commit()

    logger.info(
        "[DB] committed %s bundles",
        len(synced_bundles),
    )

    return success_count, failed_batches


# --------------------------------------------------
# Bundle saving
# --------------------------------------------------

async def save_league_bundle_to_db(
    db: AsyncSession,
    bundle: dict,
    commit: bool = True,
) -> bool:
    try:
        league_id = bundle["league_id"]

        if bundle.get("transactions_only"):
            # Known league — only save new transactions
            await _save_transactions(db, bundle.get("transactions", []), league_id)
            await _backfill_traded_picks(
                db,
                league_id,
                bundle.get("traded_picks", []),
            )
            await _save_playoff_matchups(
                db,
                bundle.get("winners_bracket", []),
                bundle.get("losers_bracket", []),
                league_id,
            )
            await db.flush()
            return True

        # New league — full save
        league_dict = transformers.league_to_db(bundle["league"], True)

        user_dicts = [
            transformers.user_to_db(u, True)
            for u in bundle.get("users", [])
        ]

        roster_dicts = [
            transformers.roster_to_db(r, True)
            for r in bundle.get("rosters", [])
        ]

        # Map per-user is_owner flags from the raw users payload onto
        # the corresponding roster dicts. Sleeper returns is_owner on the
        # user objects, but that flag is actually roster-specific. When
        # present in the user payload, propagate it into the roster rows
        # so we persist commissioner status per-roster (and per-league).
        user_is_owner_map = {}
        for u in bundle.get("users", []) or []:
            try:
                # support both pydantic model and plain dict
                uid = str(u.user_id) if hasattr(u, "user_id") else str(u.get("user_id"))
                is_owner_val = getattr(u, "is_owner", None) if hasattr(u, "is_owner") else u.get("is_owner")
                user_is_owner_map[uid] = bool(is_owner_val) if is_owner_val is not None else None
            except Exception:
                continue

        for r in roster_dicts:
            owner = r.get("owner_id")
            if owner:
                r["is_owner"] = user_is_owner_map.get(str(owner), None)

        draft_dicts = [
            transformers.draft_to_db(d, True)
            for d in bundle.get("drafts", [])
        ]

        # Ensure orphaned roster owners get a placeholder user row
        user_ids = {str(u["user_id"]) for u in user_dicts}
        for r in roster_dicts:
            owner = r.get("owner_id")
            if owner and str(owner) not in user_ids:
                user_dicts.append({
                    "user_id": str(owner),
                    "username": f"orphan_{owner[:8]}",
                    "display_name": "Orphan",
                    "avatar": None,
                    "is_placeholder": True,
                })
                user_ids.add(str(owner))

        if league_dict:
            await _bulk_upsert(db, model.League, [league_dict], "league_id")

        if user_dicts:
            await _bulk_upsert(db, model.User, user_dicts, "user_id")

        if roster_dicts:
            await _bulk_upsert(
                db,
                model.Roster,
                roster_dicts,
                ["league_id", "roster_id"],
            )

        if draft_dicts:
            await _bulk_upsert(
                db,
                model.Draft,
                draft_dicts,
                "draft_id",
            )

        await _save_draft_selections(
            db,
            drafts=bundle.get("drafts", []),
            draft_picks_by_draft_id=(
                bundle.get("draft_picks_by_draft_id", {})
            ),
            league_dict=league_dict,
        )

        await _save_transactions(db, bundle.get("transactions", []), league_id)
        await _backfill_traded_picks(
            db,
            league_id,
            bundle.get("traded_picks", []),
        )
        await _save_playoff_matchups(
            db,
            bundle.get("winners_bracket", []),
            bundle.get("losers_bracket", []),
            league_id,
        )

        await db.flush()

        if commit:
            await db.commit()

        return True

    except Exception as e:
        logger.error(f"save bundle failed: {e}", exc_info=True)
        return False


# --------------------------------------------------
# Transaction saving (shared between both paths)
# --------------------------------------------------

async def _save_transactions(
    db: AsyncSession,
    transactions: list,
    league_id: str,
) -> None:
    """
    Upserts transaction metadata for every trade so fields such as status
    remain current, while only inserting movement/pick/waiver children once.
    """

    trades = [
        transaction
        for transaction in transactions
        if transaction.type == "trade"
    ]

    if not trades:
        return

    incoming_ids = [
        transaction.transaction_id
        for transaction in trades
    ]

    result = await db.execute(
        select(
            model.Transaction.transaction_id,
        ).where(
            model.Transaction.transaction_id.in_(
                incoming_ids,
            )
        )
    )

    existing_transaction_ids = set(
        result.scalars().all(),
    )

    transaction_dicts = []
    movement_dicts = []
    waiver_dicts = []
    pick_dicts = []

    for transaction in trades:
        transaction_dict, movements, waivers, picks = (
            transformers.tx_to_db(
                transaction,
                league_id,
                True,
            )
        )

        # Always upsert transaction metadata so status stays fresh.
        transaction_dicts.append(
            transaction_dict,
        )

        # Child asset movement rows should only be inserted once.
        if (
            transaction.transaction_id
            in existing_transaction_ids
        ):
            continue

        movement_dicts.extend(
            movements,
        )

        waiver_dicts.extend(
            waivers,
        )

        pick_dicts.extend(
            picks,
        )

    if transaction_dicts:
        await _bulk_upsert(
            db,
            model.Transaction,
            transaction_dicts,
            "transaction_id",
        )

    if movement_dicts:
        await db.execute(
            insert(
                model.Movement,
            ).values(
                movement_dicts,
            )
        )

    if waiver_dicts:
        await db.execute(
            insert(
                model.WaiverBudget,
            ).values(
                waiver_dicts,
            )
        )

    if pick_dicts:
        await db.execute(
            insert(
                model.TradedPick,
            ).values(
                pick_dicts,
            )
        )


async def _save_draft_selections(
    db: AsyncSession,
    *,
    drafts: list,
    draft_picks_by_draft_id: dict[str, list],
    league_dict: dict,
) -> None:
    if not drafts:
        return

    selection_dicts: list[dict] = []
    draft_ids: list[str] = []

    for draft in drafts:
        raw_picks = draft_picks_by_draft_id.get(
            draft.draft_id,
            [],
        )

        if not raw_picks:
            continue

        draft_ids.append(
            draft.draft_id,
        )

        for fallback_pick_no, raw_pick in enumerate(
            raw_picks,
            start=1,
        ):
            if not isinstance(raw_pick, dict):
                continue

            selection_dicts.append(
                transformers.draft_selection_to_db(
                    raw_pick=raw_pick,
                    draft_id=draft.draft_id,
                    league_id=league_dict["league_id"],
                    season=str(draft.season),
                    total_rosters=int(
                        league_dict["total_rosters"],
                    ),
                    fallback_pick_no=fallback_pick_no,
                    return_dict=True,
                )
            )

    if draft_ids:
        await db.execute(
            model.DraftSelection.__table__.delete().where(
                model.DraftSelection.draft_id.in_(
                    draft_ids,
                )
            )
        )

    if selection_dicts:
        await db.execute(
            insert(
                model.DraftSelection,
            ).values(
                selection_dicts,
            )
        )


async def _backfill_traded_picks(
    db: AsyncSession,
    league_id: str,
    traded_picks: list,
) -> None:
    if not traded_picks:
        return

    existing = await db.execute(
        select(
            model.TradedPick.season,
            model.TradedPick.round,
            model.TradedPick.og_roster_id,
            model.TradedPick.new_roster_id,
        ).where(
            model.TradedPick.league_id == league_id,
        )
    )
    existing_keys = {
        (season, round_num, og_id, new_id)
        for season, round_num, og_id, new_id in existing.all()
    }

    new_dicts = []
    for p in traded_picks:
        key = (p.season, p.round, p.roster_id, p.owner_id)
        if key not in existing_keys:
            new_dicts.append({
                "league_id": league_id,
                "season": p.season,
                "round": p.round,
                "new_roster_id": p.owner_id,
                "old_roster_id": p.previous_owner_id,
                "og_roster_id": p.roster_id,
            })

    if new_dicts:
        await db.execute(
            insert(model.TradedPick).values(new_dicts)
        )


def _playoff_matchup_to_db(
    *,
    matchup,
    league_id: str,
    bracket_type: str,
) -> dict:
    return {
        "league_id": league_id,
        "bracket_type": bracket_type,
        "round": matchup.r,
        "matchup_id": matchup.m,
        "team_one_roster_id": matchup.t1,
        "team_two_roster_id": matchup.t2,
        "team_one_from_winner_matchup_id": (
            matchup.t1_from.w
            if matchup.t1_from is not None
            else None
        ),
        "team_one_from_loser_matchup_id": (
            matchup.t1_from.l
            if matchup.t1_from is not None
            else None
        ),
        "team_two_from_winner_matchup_id": (
            matchup.t2_from.w
            if matchup.t2_from is not None
            else None
        ),
        "team_two_from_loser_matchup_id": (
            matchup.t2_from.l
            if matchup.t2_from is not None
            else None
        ),
        "winner_roster_id": matchup.w,
        "loser_roster_id": matchup.l,
        "placement": matchup.p,
    }


async def _save_playoff_matchups(
    db: AsyncSession,
    winners_bracket: list,
    losers_bracket: list,
    league_id: str,
) -> None:
    matchup_dicts = [
        _playoff_matchup_to_db(
            matchup=matchup,
            league_id=league_id,
            bracket_type="winners",
        )
        for matchup in winners_bracket or []
    ] + [
        _playoff_matchup_to_db(
            matchup=matchup,
            league_id=league_id,
            bracket_type="losers",
        )
        for matchup in losers_bracket or []
    ]

    if not matchup_dicts:
        return

    await _bulk_upsert(
        db,
        model.PlayoffMatchup,
        matchup_dicts,
        [
            "league_id",
            "bracket_type",
            "round",
            "matchup_id",
        ],
    )


# --------------------------------------------------
# Sync state management
# --------------------------------------------------

async def _update_sync_states(
    *,
    db: AsyncSession,
    bundles: list[dict],
) -> None:
    """
    Updates daily freshness timestamps only after bundle data was
    successfully saved.
    """

    now = datetime.now()

    transaction_rows = [
        {
            "league_id": bundle["league_id"],
            "last_synced_week": bundle.get(
                "synced_week",
                0,
            ),
            "last_synced_at": now,
        }
        for bundle in bundles
    ]

    tx_stmt = insert(
        model.LeagueSyncState,
    ).values(
        transaction_rows,
    )

    await db.execute(
        tx_stmt.on_conflict_do_update(
            index_elements=["league_id"],
            set_={
                "last_synced_week": tx_stmt.excluded.last_synced_week,
                "last_synced_at": tx_stmt.excluded.last_synced_at,
            },
        )
    )

    full_rows = [
        {
            "league_id": bundle["league_id"],
            "last_synced_week": bundle.get(
                "synced_week",
                0,
            ),
            "last_synced_at": now,
            "last_full_synced_at": now,
        }
        for bundle in bundles
        if not bundle.get("transactions_only")
    ]

    if full_rows:
        full_stmt = insert(
            model.LeagueSyncState,
        ).values(
            full_rows,
        )

        await db.execute(
            full_stmt.on_conflict_do_update(
                index_elements=["league_id"],
                set_={
                    "last_synced_week": full_stmt.excluded.last_synced_week,
                    "last_synced_at": full_stmt.excluded.last_synced_at,
                    "last_full_synced_at": full_stmt.excluded.last_full_synced_at,
                },
            )
        )


# --------------------------------------------------
# Other helpers (unchanged)
# --------------------------------------------------

async def fetch_league_bundle_full(league, curr_week, sleeper):
    """Legacy full-fetch used outside of sync_leagues (e.g. single league refresh)."""
    league_id = league.league_id
    if not league_id:
        return None

    try:
        league_obj, users, rosters, drafts, tx_lists = await asyncio.gather(
            sleeper.read.get_league(league_id),
            sleeper.read.get_users(league_id),
            sleeper.read.get_rosters(league_id),
            sleeper.read.get_drafts_league(league_id),
            asyncio.gather(
                *[
                    sleeper.read.get_transactions(league_id, week)
                    for week in range(1, curr_week + 1)
                ],
                return_exceptions=True,
            ),
        )

        trades = [
            tx
            for batch in tx_lists
            if isinstance(batch, list)
            for tx in batch
        ]

        return {
            "league_id": league_id,
            "league": league_obj,
            "users": users,
            "rosters": rosters,
            "drafts": drafts,
            "transactions": trades,
            "transactions_only": False,
        }

    except Exception as e:
        logger.error(f"[BUNDLE ERROR] league={league_id} err={e}", exc_info=True)
        return None


async def get_league_context(db: AsyncSession, league_id: str):
    league = await db.get(model.League, league_id)

    rosters = (
        await db.execute(
            select(model.Roster).where(model.Roster.league_id == league_id)
        )
    ).scalars().all()

    projections = (
        await db.execute(
            select(model.PlayerProjection).where(
                model.PlayerProjection.season == int(league.season)
            )
        )
    ).scalars().all()

    return {
        "league": league,
        "rosters": rosters,
        "projections": projections,
    }


async def get_user_leagues(db: AsyncSession, username: str):
    result = await db.execute(
        select(model.League, model.Roster)
        .join(model.Roster, model.Roster.league_id == model.League.league_id)
        .join(model.User, model.User.user_id == model.Roster.owner_id)
        .where(model.User.display_name == username)
    )
    return result.all()


async def get_owned_leagues_by_sleeper_user_id(
    db: AsyncSession,
    sleeper_user_id: str,
):
    result = await db.execute(
        select(model.League, model.Roster)
        .join(
            model.Roster,
            model.Roster.league_id == model.League.league_id,
        )
        .where(
            model.Roster.owner_id == sleeper_user_id,
            model.Roster.is_owner == True,
        )
    )
    return result.all()


async def get_league_with_rosters(db, league_id: str):
    result = await db.execute(
        select(model.League, model.Roster)
        .join(model.Roster, model.Roster.league_id == model.League.league_id)
        .where(model.League.league_id == league_id)
    )
    return result.all()
