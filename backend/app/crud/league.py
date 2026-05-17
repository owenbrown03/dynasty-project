import asyncio
from typing import List, Set, Optional, Any
from sqlmodel import Session, select
from sqlalchemy import inspect
import logging

from app.schemas import schemas 
from app.services import transformers
from app.models import models
from app.services import sleeper
from app.crud.base import _bulk_upsert

logger = logging.getLogger(__name__)

def get_league_map(db: Session) -> dict[str, str]:
    """Returns a dict of {league_id: league_name}"""
    result = db.exec(select(models.League.league_id, models.League.name)).all()
    return {l.league_id: l.name for l in result}

def get_existing_leagues(db: Session, league_ids: List[str]) -> Set[str]:
    """Given a list of league IDs, returns a set of IDs that already exist in the DB."""
    statement = select(models.League.league_id).where(models.League.league_id.in_(league_ids))
    existing_leagues = db.exec(statement).all()
    return {l for l in existing_leagues}

async def sync_new_leagues(db: Session, raw_leagues: list[dict]) -> dict:
    unique_leagues = {l['league_id']: l for l in raw_leagues if l}
    incoming_ids = list(unique_leagues.keys())
    
    loop = asyncio.get_running_loop()
    existing_ids = await loop.run_in_executor(
        None, 
        get_existing_leagues, 
        db, 
        incoming_ids
    )
    
    leagues_to_sync = [
        l for l_id, l in unique_leagues.items() 
        if l_id not in existing_ids
    ]

    if not leagues_to_sync:
        logger.info("Sync verification skipped: All incoming leagues are already tracked in the database.")
        return {"status": "skipped", "synced_count": 0}

    total_leagues = len(leagues_to_sync)
    logger.info(f"Initiating network scrape workflow for {total_leagues} un-tracked leagues.")
    
    status_result = {"status": "failed", "synced_count": 0}
    
    try:
        processed_fetches = 0
        
        async def fetch_with_progress(league_data):
            nonlocal processed_fetches
            try:
                return await fetch_league_bundle(league_data)
            finally:
                processed_fetches += 1
                if total_leagues >= 4 and processed_fetches % max(1, total_leagues // 4) == 0:
                    logger.info(f"[Network Ingestion] Scraped {processed_fetches}/{total_leagues} leagues from Sleeper API.")

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
            nested = db.begin_nested()
            try:
                for bundle in chunk:
                    success = save_league_bundle_to_db(db, bundle, commit=False)
                    if not success:
                        logger.warning("Aborting sub-transaction chunk due to internal parsing layout failure.")
                        nested.rollback()
                        break
                else:
                    nested.commit()
                    success_count += len(chunk)
            except Exception as chunk_err:
                logger.error(f"Nested transactional context crash encountered: {chunk_err}", exc_info=True)
                nested.rollback()
                        
            db.commit()
            
            current_processed = min(i + batch_size, total_valid)
            logger.info(f"[Database Commit] Flushed {current_processed}/{total_valid} packages down to storage tier.")
        
        status_result = {"status": "completed", "synced_count": success_count}
        logger.info(f"Sync event complete. Successfully integrated {success_count} leagues into core database schemas.")
            
    except Exception as e:
        logger.error(f"Critical engineering fault identified inside sync execution cycle: {str(e)}", exc_info=True)
        raise e

    return status_result

async def fetch_league_bundle(league_dict: dict) -> Optional[dict]:
    """Pure network request worker. Fetches the detailed league metadata along with sub-assets."""
    league_id = league_dict.get("league_id")
    try:
        tasks = [
            sleeper.get_league(league_id),
            sleeper.get_users(league_id),
            sleeper.get_rosters(league_id),
            sleeper.get_transactions(league_id, 1),
            sleeper.get_drafts_league(league_id)
        ]
        full_league, users, rosters, trades, drafts = await asyncio.gather(*tasks)
        
        return {
            "league_json": full_league or league_dict, 
            "users_json": users,
            "rosters_json": rosters,
            "trades_json": trades,
            "drafts_json": drafts
        }
    except Exception as e:
        logger.error(f"Sleeper API download failed for league {league_id}: {e}")
        return None

def save_league_bundle_to_db(db: Session, bundle: dict, commit: bool = True) -> bool:
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
            existing_tx_ids = set(db.exec(statement).all())

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

        _bulk_upsert(db, models.League, [db_league_dict], "league_id")
        
        if db_user_dicts:
            _bulk_upsert(db, models.User, db_user_dicts, "user_id")
            
        _bulk_upsert(db, models.Roster, db_roster_dicts, ["league_id", "roster_id"])
        _bulk_upsert(db, models.Transaction, db_transaction_dicts, "transaction_id")
                
        if db_movement_dicts: 
            db.bulk_insert_mappings(inspect(models.Movement), db_movement_dicts)
        if db_waiver_dicts: 
            db.bulk_insert_mappings(inspect(models.WaiverBudget), db_waiver_dicts)
        if db_pick_dicts: 
            db.bulk_insert_mappings(inspect(models.TradedPick), db_pick_dicts)

        if commit:
            db.commit()
        else:
            db.flush()
        return True
    
    except Exception as e:
        if commit:
            db.rollback()
        logger.exception(f"CRITICAL DATA MATRIX ALIGNMENT FAULT for league {league_id}")
        return False