import logging, asyncio
from typing import List, Set

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.models.db.sleeper import api as model
from app.services.sleeper import transformers
from app.crud.base import _bulk_upsert
from app.core.concurrency import bounded_gather
from app.analytics.war.redraft.cache import clear_league_war_cache

logger = logging.getLogger(__name__)

async def get_league_map(db: AsyncSession) -> dict[str, str]:
    """Returns {league_id: league_name}"""
    result = await db.execute(
        select(model.League.league_id, model.League.name)
    )
    return {league_id: name for league_id, name in result.all()}


async def get_existing_leagues(db: AsyncSession, league_ids: List[str]) -> Set[str]:
    stmt = select(model.League.league_id).where(
        model.League.league_id.in_(league_ids)
    )
    result = await db.execute(stmt)
    return set(result.scalars().all())


async def sync_leagues(db, raw_leagues, curr_week, sleeper):
    curr_week = max(curr_week, 1)

    leagues = {
        l.league_id: l
        for l in raw_leagues
        if l and l.league_id
    }.values()

    leagues = list(leagues)

    if not leagues:
        return {"status": "skipped", "synced_count": 0}

    logger.info(f"Starting ingestion for {len(leagues)} leagues")

    bundles = await bounded_gather([fetch_league_bundle(l, curr_week, sleeper) for l in leagues])

    bundles = [
        b for b in bundles
        if isinstance(b, dict) and b.get("league")
    ]

    if not bundles:
        return {"status": "failed", "synced_count": 0}

    logger.info(f"[DB] ingesting {len(bundles)} bundles")

    success_count = 0
    failed_batches = 0
    batch_size = 100

    for i in range(0, len(bundles), batch_size):
        chunk = bundles[i:i + batch_size]

        try:
            for bundle in chunk:
                ok = await save_league_bundle_to_db(db, bundle, commit=False)
                if not ok:
                    raise RuntimeError("bundle save failed")

            await db.flush()
            success_count += len(chunk)

        except Exception as e:
            failed_batches += 1
            logger.error(f"[DB BATCH ERROR] {e}", exc_info=True)

    await db.commit()

    logger.info(
        f"[DB] committed {len(bundles)} bundles"
    )

    for bundle in bundles:

        league = bundle["league"]

        clear_league_war_cache(
            league.league_id,
            int(league.season),
        )


    return {
        "status": "completed",
        "synced_count": success_count,
        "failed_batches": failed_batches
    }

async def fetch_league_bundle(league, curr_week, sleeper):
    league_id = league.league_id
    if not league_id:
        return None

    try:
        league, users, rosters, drafts, tx_lists = await asyncio.gather(
            sleeper.read.get_league(league_id),
            sleeper.read.get_users(league_id),
            sleeper.read.get_rosters(league_id),
            sleeper.read.get_drafts_league(league_id),
            asyncio.gather(
                *[
                    sleeper.read.get_transactions(league_id, week)
                    for week in range(1, curr_week + 1)
                ],
                return_exceptions=True
            )
        )

        trades = [
            tx
            for batch in tx_lists
            if isinstance(batch, list)
            for tx in batch
        ]

        return {
            "league": league,
            "users": users,
            "rosters": rosters,
            "drafts": drafts,
            "transactions": trades,
        }

    except Exception as e:
        logger.error(f"[BUNDLE ERROR] league={league_id} err={e}", exc_info=True)
        return None
    

async def save_league_bundle_to_db(db: AsyncSession, bundle: dict, commit: bool = True) -> bool:

    try:
        league_id = bundle["league"].league_id

        league_dict = transformers.league_to_db(bundle["league"], True)

        user_dicts = [
            transformers.user_to_db(u, True)
            for u in bundle.get("users", [])
        ]

        roster_dicts = [
            transformers.roster_to_db(r, True)
            for r in bundle.get("rosters", [])
        ]

        user_ids = {str(u["user_id"]) for u in user_dicts}

        for r in roster_dicts:
            owner = r.get("owner_id")
            if owner and str(owner) not in user_ids:
                user_dicts.append({
                    "user_id": str(owner),
                    "username": f"orphan_{owner[:8]}",
                    "display_name": "Orphan",
                    "avatar": None
                })
                user_ids.add(str(owner))

        tx_dicts = []
        movement_dicts = []
        waiver_dicts = []
        pick_dicts = []

        incoming = [
            t.transaction_id
            for t in bundle.get("transactions", [])
            if t.type == "trade"
        ]

        existing = set()
        if incoming:
            res = await db.execute(
                select(model.Transaction.transaction_id).where(
                    model.Transaction.transaction_id.in_(incoming)
                )
            )
            existing = set(res.scalars().all())

        for tx in bundle.get("transactions", []):
            if tx.type != "trade":
                continue
            if tx.transaction_id in existing:
                continue

            tx_d, mv, wv, pk = transformers.tx_to_db(
                tx, league_id, True
            )

            tx_dicts.append(tx_d)
            movement_dicts.extend(mv)
            waiver_dicts.extend(wv)
            pick_dicts.extend(pk)

        if league_dict:
            await _bulk_upsert(db, model.League, [league_dict], "league_id")

        if user_dicts:
            await _bulk_upsert(db, model.User, user_dicts, "user_id")

        if roster_dicts:
            await _bulk_upsert(
                db,
                model.Roster,
                roster_dicts,
                ["league_id", "roster_id"]
            )

        if tx_dicts:
            await _bulk_upsert(
                db,
                model.Transaction,
                tx_dicts,
                "transaction_id"
            )

        if movement_dicts:
            await db.execute(insert(model.Movement).values(movement_dicts))

        if waiver_dicts:
            await db.execute(insert(model.WaiverBudget).values(waiver_dicts))

        if pick_dicts:
            await db.execute(insert(model.TradedPick).values(pick_dicts))

        await db.flush()

        return True

    except Exception as e:
        logger.error(f"save bundle failed: {e}", exc_info=True)
        return False
    

async def get_league_context(db: AsyncSession, league_id: str):
    league = await db.get(
        model.League,
        league_id,
    )

    rosters = (
        await db.execute(
            select(model.Roster).where(
                model.Roster.league_id == league_id
            )
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
        select(
            model.League,
            model.Roster,
        )
        .join(
            model.Roster,
            model.Roster.league_id == model.League.league_id
        )
        .join(
            model.User,
            model.User.user_id == model.Roster.owner_id
        )
        .where(
            model.User.display_name == username
        )
    )

    return result.all()

async def get_league_with_rosters(db, league_id: str):
    result = await db.execute(
        select(
            model.League,
            model.Roster,
        )
        .join(
            model.Roster,
            model.Roster.league_id == model.League.league_id
        )
        .where(
            model.League.league_id == league_id
        )
    )

    return result.all()