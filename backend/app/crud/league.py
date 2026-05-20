import logging, asyncio
from typing import List, Set, Optional
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.schemas import schemas 
from app.services import transformers
from app.models import models
from app.services import sleeper
from app.crud.base import _bulk_upsert

logger = logging.getLogger(__name__)

async def get_league_map(db: AsyncSession) -> dict[str, str]:
    """Returns a dict of {league_id: league_name}"""
    result = await db.execute(select(models.League.league_id, models.League.name))
    return {l.league_id: l.name for l in result.all()}

async def get_existing_leagues(db: AsyncSession, league_ids: List[str]) -> Set[str]:
    """Given a list of league IDs, returns a set of IDs that already exist in the DB."""
    stmt = select(models.League.league_id).where(models.League.league_id.in_(league_ids))
    result = await db.execute(stmt)
    return {l for l in result.scalars().all()}

async def sync_leagues(db: AsyncSession, raw_leagues: list[dict]) -> dict:
    state = await sleeper.get_NFL_state()
    curr_week = schemas.NFLState(**state).week
    if curr_week < 1:
        curr_week = 1
    
    unique_leagues = {l['league_id']: l for l in raw_leagues if l}
    leagues_to_sync = list(unique_leagues.values())

    if not leagues_to_sync:
        logger.info("Sync leagues skipped: No valid leagues provided in payload.")
        return {"status": "skipped", "synced_count": 0}

    total_leagues = len(leagues_to_sync)
    logger.info(f"Initiating network scrape workflow for {total_leagues} leagues.")
    
    status_result = {"status": "failed", "synced_count": 0}
    
    try:
        processed_fetches = 0
        progress_interval = 10
        async def fetch_with_progress(league_data):
            nonlocal processed_fetches
            try:
                return await fetch_league_bundle(league_data, curr_week)
            finally:
                processed_fetches += 1
                if total_leagues >= progress_interval and processed_fetches % max(1, total_leagues // progress_interval) == 0:
                    logger.info(f"[Network Ingestion] Scraped {processed_fetches}/{total_leagues} leagues from Sleeper API ({(processed_fetches / total_leagues) * 100:.1f}%)")

        api_tasks = [fetch_with_progress(l) for l in leagues_to_sync]
        bundles = await asyncio.gather(*api_tasks, return_exceptions=True)
        
        valid_bundles = [b for b in bundles if isinstance(b, dict)]
        total_valid = len(valid_bundles)

        if not valid_bundles:
            logger.warning("Network ingestion failed: No valid league bundles could be scraped from the API.")
            return {"status": "failed", "synced_count": 0}
            
        logger.info(f"Ingestion successful: {total_valid} data packages ready for database translation matrix.")

        success_count = 0
        batch_size = 100
        
        for i in range(0, total_valid, batch_size):
            chunk = valid_bundles[i : i + batch_size]
            
            async with db.begin_nested():
                try:
                    for bundle in chunk:
                        success = await save_league_bundle_to_db(db, bundle, commit=False)
                        if not success:
                            raise Exception("Sub-transaction bundle failure. Rolling back chunk.")
                    
                    success_count += len(chunk)
                    
                    await db.flush()
                    
                except Exception as chunk_err:
                    logger.error(f"Nested context crash encountered, rolling back this chunk of {batch_size}: {chunk_err}")
                    continue 
            
            current_processed = min(i + batch_size, total_valid)
            logger.info(f"[Database Batch] Flushed {current_processed}/{total_valid} packages down to storage tier.")
        
        await db.commit()
            
        status_result = {"status": "completed", "synced_count": success_count}
        logger.info(f"Sync event complete. Successfully integrated {success_count} leagues into core database schemas.")
            
    except Exception as e:
        logger.error(f"Critical engineering fault identified inside sync execution cycle: {str(e)}", exc_info=True)
        raise e

    return status_result

async def fetch_league_bundle(league_dict: dict, curr_week: int) -> Optional[dict]:
    league_id = league_dict.get("league_id")
    if not league_id:
        logger.error("Network download aborted: Missing 'league_id' in payload.")
        return None

    try:
        core_tasks = [
            sleeper.get_league(league_id),
            sleeper.get_users(league_id),
            sleeper.get_rosters(league_id),
            sleeper.get_drafts_league(league_id)
        ]
        
        core_results = await asyncio.gather(*core_tasks, return_exceptions=True)
        
        for idx, res in enumerate(core_results):
            if isinstance(res, Exception):
                logger.error(f"[Core API Failure] Task index {idx} failed for league {league_id}: {str(res)}")

        league = core_results[0] if not isinstance(core_results[0], Exception) else None
        users = core_results[1] if not isinstance(core_results[1], Exception) else []
        rosters = core_results[2] if not isinstance(core_results[2], Exception) else []
        drafts = core_results[3] if not isinstance(core_results[3], Exception) else []

        if not league or not isinstance(league, dict):
            logger.warning(f"Aborting downstream steps: Failed to fetch valid league metadata object for {league_id}.")
            return None
        
        trade_tasks = [sleeper.get_transactions(league_id, week) for week in range(1, curr_week + 1)]
        trade_results = await asyncio.gather(*trade_tasks, return_exceptions=True)
        
        trades = []
        for week_idx, week_res in enumerate(trade_results, start=1):
            if isinstance(week_res, Exception):
                logger.error(f"[Trade API Failure] Could not pull Week {week_idx} transactions for league {league_id}: {week_res}")
                continue
            if isinstance(week_res, list):
                trades.extend(week_res)

        return {
            "league_json": league, 
            "users_json": users,
            "rosters_json": rosters,
            "trades_json": trades,
            "drafts_json": drafts
        }
        
    except Exception as e:
        logger.error(f"Sleeper API historical download failed for league {league_id}: {e}", exc_info=True)
        return None

async def save_league_bundle_to_db(db: AsyncSession, bundle: dict, commit: bool = True) -> bool:
    league_id = bundle["league_json"].get("league_id")
    try:
        league_schema = schemas.SleeperLeague.model_validate(bundle["league_json"])
        db_league_dict = transformers.league_to_db(league_schema, return_dict=True)

        db_roster_dicts = [
            transformers.roster_to_db(schemas.SleeperRoster.model_validate(r), return_dict=True) 
            for r in (bundle.get("rosters_json") or []) if r
        ]

        db_user_dicts = [
            transformers.user_to_db(schemas.SleeperUser.model_validate(u), return_dict=True)
            for u in (bundle.get("users_json") or []) if u
        ]

        known_user_ids = {str(u["user_id"]) for u in db_user_dicts}
        for roster in db_roster_dicts:
            owner_id = roster.get("owner_id")
            if owner_id and str(owner_id) not in known_user_ids:
                db_user_dicts.append({
                    "user_id": str(owner_id),
                    "username": f"orphan_{owner_id[:8]}",
                    "display_name": "Orphan Roster Placeholder",
                    "avatar": None,
                    "is_owner": False
                })
                known_user_ids.add(str(owner_id))

        db_transaction_dicts = []
        db_movement_dicts = []
        db_waiver_dicts = []
        db_pick_dicts = []

        incoming_tx_ids = [
            t['transaction_id'] for t in bundle.get('trades_json', []) 
            if t.get('type') == 'trade' and 'transaction_id' in t
        ]
        existing_tx_ids = set()
        if incoming_tx_ids:
            statement = select(models.Transaction.transaction_id).where(
                models.Transaction.transaction_id.in_(incoming_tx_ids)
            )
            result = await db.execute(statement)
            existing_tx_ids = set(result.scalars().all())

        for t_json in (bundle.get("trades_json") or []):
            if not t_json or t_json.get('type') != 'trade':
                continue
            tx_id = t_json.get('transaction_id')
            if tx_id in existing_tx_ids:
                continue

            tx_schema = schemas.SleeperTransaction.model_validate(t_json)
            tx_dict, movements, waivers, picks = transformers.tx_to_db(tx_schema, league_id, return_dict=True)
            
            db_transaction_dicts.append(tx_dict)
            db_movement_dicts.extend(movements)
            db_waiver_dicts.extend(waivers)
            db_pick_dicts.extend(picks)
        
        if db_league_dict:
            await _bulk_upsert(db, models.League, [db_league_dict], "league_id")
        if db_user_dicts:
            await _bulk_upsert(db, models.User, db_user_dicts, "user_id")
        if db_roster_dicts:
            await _bulk_upsert(db, models.Roster, db_roster_dicts, ["league_id", "roster_id"])
        if db_transaction_dicts:
            await _bulk_upsert(db, models.Transaction, db_transaction_dicts, "transaction_id")
            
        if db_movement_dicts: 
            await db.execute(insert(models.Movement).values(db_movement_dicts))
        if db_waiver_dicts: 
            await db.execute(insert(models.WaiverBudget).values(db_waiver_dicts))
        if db_pick_dicts: 
            await db.execute(insert(models.TradedPick).values(db_pick_dicts))

        await db.flush()
        return True
    
    except Exception as e:
        return False