import logging
import asyncio
from datetime import datetime
from typing import List, Set

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.models.db.sleeper import api as model
from app.services.sleeper import transformers
from app.crud.base import _bulk_upsert
from app.core.concurrency import bounded_gather

logger = logging.getLogger(__name__)


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


async def get_sync_states(db: AsyncSession, league_ids: List[str]) -> dict[str, int]:
    """Returns {league_id: last_synced_week} for all known leagues."""
    result = await db.execute(
        select(
            model.LeagueSyncState.league_id,
            model.LeagueSyncState.last_synced_week,
        ).where(
            model.LeagueSyncState.league_id.in_(league_ids)
        )
    )
    return {league_id: week for league_id, week in result.all()}


# --------------------------------------------------
# Core sync entry point
# --------------------------------------------------

async def sync_leagues(db, raw_leagues, curr_week, sleeper):
    curr_week = max(curr_week, 1)

    leagues = list(
        {l.league_id: l for l in raw_leagues if l and l.league_id}.values()
    )

    if not leagues:
        return {"status": "skipped", "synced_count": 0}

    logger.info(f"Starting ingestion for {len(leagues)} leagues")

    all_league_ids = [l.league_id for l in leagues]

    # Load existing league IDs and sync states in one pass
    existing_ids, sync_states = await asyncio.gather(
        get_existing_leagues(db, all_league_ids),
        get_sync_states(db, all_league_ids),
    )

    bundles = await bounded_gather([
        fetch_league_bundle(l, curr_week, sleeper, existing_ids, sync_states)
        for l in leagues
    ])

    # Filter out None (skipped leagues with no new data) and exceptions
    bundles = [
        b for b in bundles
        if isinstance(b, dict)
    ]

    if not bundles:
        return {"status": "skipped", "synced_count": 0, "reason": "no_new_data"}

    logger.info(f"[DB] ingesting {len(bundles)} bundles")

    success_count = 0
    failed_batches = 0
    batch_size = 100
    synced_league_ids = []

    for i in range(0, len(bundles), batch_size):
        chunk = bundles[i:i + batch_size]

        try:
            for bundle in chunk:
                ok = await save_league_bundle_to_db(db, bundle, commit=False)
                if not ok:
                    raise RuntimeError("bundle save failed")

            await db.flush()
            success_count += len(chunk)
            synced_league_ids.extend(b["league_id"] for b in chunk)

        except Exception as e:
            failed_batches += 1
            logger.error(f"[DB BATCH ERROR] {e}", exc_info=True)

    # Update sync state for all successfully saved leagues
    if synced_league_ids:
        await _update_sync_states(db, synced_league_ids, curr_week)

    await db.commit()

    logger.info(f"[DB] committed {len(bundles)} bundles")

    return {
        "status": "completed",
        "synced_count": success_count,
        "failed_batches": failed_batches,
    }


# --------------------------------------------------
# Bundle fetching
# --------------------------------------------------

async def fetch_league_bundle(
    league,
    curr_week: int,
    sleeper,
    existing_ids: Set[str],
    sync_states: dict[str, int],
):
    league_id = league.league_id
    if not league_id:
        return None

    is_new = league_id not in existing_ids
    last_synced_week = sync_states.get(league_id, 0)
    weeks_to_fetch = list(range(last_synced_week + 1, curr_week + 1))

    if not is_new and not weeks_to_fetch:
        # Already up to date — nothing to do
        logger.debug(f"[SKIP] {league_id} already synced to week {last_synced_week}")
        return None

    try:
        if is_new:
            # Full fetch — league we've never seen before
            league_obj, users, rosters, drafts, tx_lists = await asyncio.gather(
                sleeper.read.get_league(league_id),
                sleeper.read.get_users(league_id),
                sleeper.read.get_rosters(league_id),
                sleeper.read.get_drafts_league(league_id),
                asyncio.gather(
                    *[
                        sleeper.read.get_transactions(league_id, week)
                        for week in weeks_to_fetch
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

        else:
            # Known league — only fetch new transaction weeks
            tx_lists = await asyncio.gather(
                *[
                    sleeper.read.get_transactions(league_id, week)
                    for week in weeks_to_fetch
                ],
                return_exceptions=True,
            )

            trades = [
                tx
                for batch in tx_lists
                if isinstance(batch, list)
                for tx in batch
            ]

            return {
                "league_id": league_id,
                "league": None,
                "users": [],
                "rosters": [],
                "drafts": [],
                "transactions": trades,
                "transactions_only": True,
            }

    except Exception as e:
        logger.error(f"[BUNDLE ERROR] league={league_id} err={e}", exc_info=True)
        return None


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

        await _save_transactions(db, bundle.get("transactions", []), league_id)

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
    trades = [t for t in transactions if t.type == "trade"]

    if not trades:
        return

    incoming_ids = [t.transaction_id for t in trades]

    res = await db.execute(
        select(model.Transaction.transaction_id).where(
            model.Transaction.transaction_id.in_(incoming_ids)
        )
    )
    existing = set(res.scalars().all())

    tx_dicts = []
    movement_dicts = []
    waiver_dicts = []
    pick_dicts = []

    for tx in trades:
        if tx.transaction_id in existing:
            continue

        tx_d, mv, wv, pk = transformers.tx_to_db(tx, league_id, True)
        tx_dicts.append(tx_d)
        movement_dicts.extend(mv)
        waiver_dicts.extend(wv)
        pick_dicts.extend(pk)

    if tx_dicts:
        await _bulk_upsert(db, model.Transaction, tx_dicts, "transaction_id")

    if movement_dicts:
        await db.execute(insert(model.Movement).values(movement_dicts))

    if waiver_dicts:
        await db.execute(insert(model.WaiverBudget).values(waiver_dicts))

    if pick_dicts:
        await db.execute(insert(model.TradedPick).values(pick_dicts))


# --------------------------------------------------
# Sync state management
# --------------------------------------------------

async def _update_sync_states(
    db: AsyncSession,
    league_ids: List[str],
    week: int,
) -> None:
    now = datetime.utcnow()
    rows = [
        {
            "league_id": league_id,
            "last_synced_week": week,
            "last_synced_at": now,
        }
        for league_id in league_ids
    ]
    await _bulk_upsert(db, model.LeagueSyncState, rows, "league_id")


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


async def get_league_with_rosters(db, league_id: str):
    result = await db.execute(
        select(model.League, model.Roster)
        .join(model.Roster, model.Roster.league_id == model.League.league_id)
        .where(model.League.league_id == league_id)
    )
    return result.all()