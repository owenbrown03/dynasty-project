from sqlalchemy.orm import Session
from dataclasses import dataclass
from typing import Set, Tuple
import asyncio, logging, sleeper, schemas, models, crud, mappers

logger = logging.getLogger(__name__)

@dataclass
class Info:
    main_user: schemas.SleeperUser
    state: schemas.NFLState
    db_leagues: Set[str]
    db_users: Set[str]
    db_rosters: Set[Tuple[str, str]] # roster_id, owner_id
    db_txs: Set[str]
    db_drafts: Set[str]

async def info_sync(db, username: str) -> Info:
    user_task = sleeper.get_username_details(username)
    state_task = sleeper.get_NFL_state()
    
    user_data, state_data = await asyncio.gather(user_task, state_task)

    return Info(
        main_user=schemas.SleeperUser(**user_data),
        state=schemas.NFLState(**state_data),
        db_leagues=set(crud.read_all(db, models.League.league_id)),
        db_users=set(crud.read_all(db, models.User.user_id)),
        db_rosters=set(crud.read_all(db, models.Roster.league_id, models.Roster.owner_id)),
        db_txs=set(crud.read_all(db, models.Transaction.transaction_id)),
        db_drafts=set(crud.read_all(db, models.Draft.draft_id))
    )

async def create_lm_data(db: Session, info: 'Info'):
    await create_user_data(db, info, info.main_user.user_id)
    lms = crud.get_leaguemates(db, info.main_user.user_id)
    logger.info(f'Found {len(lms)} leaguemates.')
    tasks = [create_user_data(db, info, u) for u in lms]
    await asyncio.gather(*tasks)
    
    try:
        db.commit()
        logger.info(f'Successfully committed to the database.')
    except Exception as e:
        db.rollback()
        logger.error(f'Failed to save sync results: {e}', exc_info=True)
        raise

async def create_user_data(db: Session, info: 'Info', user_id: str):
    leaguesJSON = await sleeper.get_leagues(user_id, info.state.season)
    tasks = [get_league_data(l) for l in leaguesJSON]
    league_data = await asyncio.gather(*tasks)
    await sync_league_data(db, info, league_data)

async def get_league_data(league: dict):
    l_id = league['league_id']
    users, rosters, trades, drafts = await asyncio.gather(
        sleeper.get_users(l_id),
        sleeper.get_rosters(l_id),
        sleeper.get_transactions(l_id, 1), # NEED TO UPDATE TO DO ALL WEEKS
        sleeper.get_drafts_league(l_id)
    )
    return {
        'leagueJSON': league,
        'usersJSON': users,
        'rostersJSON': rosters,
        'tradesJSON': trades,
        'draftsJSON': drafts
    }

async def sync_league_data(db: Session, info: 'Info', league_data: list):
    l_ct = u_ct = r_ct = t_ct = d_ct = 0
    for data in league_data:  
        #league
        
        l_json = data['leagueJSON']
        if l_json['league_id'] in info.db_leagues:
            continue
        l_schema = schemas.SleeperLeague(**l_json)
        l_model = models.League(**mappers.league_to_db(l_schema))
        db.add(l_model)
        info.db_leagues.add(l_json['league_id'])
        l_ct += 1

        #users
        for u_json in data['usersJSON']:
            if u_json['user_id'] not in info.db_users:
                u_schema = schemas.SleeperUser(**u_json)
                db.add(models.User(**mappers.schema_to_db(u_schema)))
                info.db_users.add(u_json['user_id'])
                u_ct += 1

        #rosters
        for r_json in data['rostersJSON']:
            if (r_json['league_id'], r_json['owner_id']) not in info.db_rosters:
                r_schema = schemas.SleeperRoster(**r_json)
                db.add(models.Roster(**mappers.roster_to_db(r_schema)))
                info.db_rosters.add((r_json['roster_id'], r_json['owner_id']))
                r_ct += 1

        #trades
        for t_json in data['tradesJSON']:
            if t_json['type'] == 'trade' and t_json['transaction_id'] not in info.db_txs:
                t_schema = schemas.SleeperTransaction(**t_json)
                t_map, m_map, w_map, p_map = mappers.tx_to_db(t_schema, l_schema)
                t_model = models.Transaction(**t_map)
                m_models = [models.Movement(**m) for m in m_map]
                w_models = [models.WaiverBudget(**w) for w in w_map]
                p_models = [models.TradedPick(**p) for p in p_map]
                db.add(t_model)
                info.db_txs.add(t_json['transaction_id'])
                db.add_all(m_models)
                db.add_all(w_models)
                db.add_all(p_models)
                t_ct += 1

        #drafts
        for d_json in data['draftsJSON']:
            if d_json['draft_id'] not in info.db_drafts:
                d_schema = schemas.SleeperDraft(**d_json)
                db.add(models.Draft(**mappers.schema_to_db(d_schema)))
                info.db_drafts.add(d_json['draft_id'])
                d_ct += 1

    logger.info(f'Queued {l_ct} leagues, {u_ct} users, {r_ct} rosters, {t_ct} transactions, {d_ct} drafts.')