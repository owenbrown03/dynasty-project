import asyncio
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
import logging

from app.models import models
from app.schemas import schemas
from app.services import mappers, sleeper
from app.crud.base import _bulk_upsert

logger = logging.getLogger(__name__)

async def get_league_data(league: dict):
    l_id = league['league_id']
    users, rosters, trades, drafts = await asyncio.gather(
        sleeper.get_users(l_id),
        sleeper.get_rosters(l_id),
        sleeper.get_transactions(l_id, 1), #UPDATE TO DO ALL WEEKS
        sleeper.get_drafts_league(l_id)
    )
    return {
        'league_json': league,
        'users_json': users,
        'rosters_json': rosters,
        'trades_json': trades,
        'drafts_json': drafts
    }

async def sync_league_data(db: Session, league_data: list):
    to_upsert = {
        "leagues": [], "users": [], "rosters": [], 
        "transactions": [], "drafts": [], "movements": [],
        "waivers": [], "picks": []
    }

    for data in league_data:
        l_json = data['league_json']
        l_schema = schemas.SleeperLeague(**l_json)
        
        to_upsert["leagues"].append(mappers.league_to_db(l_schema))

        for u_json in data['users_json']:
            u_schema = schemas.SleeperUser(**u_json)
            to_upsert["users"].append(mappers.schema_to_db(u_schema))
                
        for r_json in data['rosters_json']:
            r_schema = schemas.SleeperRoster(**r_json)
            to_upsert["rosters"].append(mappers.roster_to_db(r_schema))

        for t_json in data['trades_json']:
            if t_json['type'] == 'trade':
                t_schema = schemas.SleeperTransaction(**t_json)
                t_map, m_map, w_map, p_map = mappers.tx_to_db(t_schema, l_schema)
                to_upsert["transactions"].append(t_map)
                to_upsert["movements"].extend(m_map)
                to_upsert["waivers"].extend(w_map)
                to_upsert["picks"].extend(p_map)

        for d_json in data['drafts_json']:
            d_schema = schemas.SleeperDraft(**d_json)
            to_upsert["drafts"].append(mappers.schema_to_db(d_schema))

    _bulk_upsert(db, models.League, to_upsert["leagues"], "league_id")
    _bulk_upsert(db, models.User, to_upsert["users"], "user_id")
    _bulk_upsert(db, models.Roster, to_upsert["rosters"], ["league_id", "owner_id"])
    _bulk_upsert(db, models.Transaction, to_upsert["transactions"], "transaction_id")
    _bulk_upsert(db, models.Draft, to_upsert["drafts"], "draft_id")
    
    if to_upsert["movements"]:
        db.bulk_insert_mappings(models.Movement, to_upsert["movements"])
    
    db.commit()
    logger.info("Sync complete. Database state updated via Upsert.")