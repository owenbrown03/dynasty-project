from sqlalchemy.orm import Session
from dataclasses import dataclass
from typing import Set, Tuple
from datetime import datetime, timedelta
import asyncio, logging, sleeper, schemas, models, crud, mappers

logger = logging.getLogger(__name__)

@dataclass
class Info:
    main_user: schemas.SleeperUser
    state: schemas.NFLState
    player_map: schemas.PlayerMap
    db_leagues: Set[str]
    db_users: Set[str]
    db_rosters: Set[Tuple[str, str]] # roster_id, owner_id
    db_txs: Set[str]
    db_drafts: Set[str]

async def info_sync(db, username: str) -> Info:
    user_task = sleeper.get_username_details(username)
    state_task = sleeper.get_NFL_state()
    user_data, state_data = await asyncio.gather(user_task, state_task)

    info = Info(
        main_user=schemas.SleeperUser(**user_data),
        state=schemas.NFLState(**state_data),
        player_map={p.player_id: p for p in crud.read_all(db, models.Player)},
        db_leagues=set(crud.read_all(db, models.League.league_id)),
        db_users=set(crud.read_all(db, models.User.user_id)),
        db_rosters=set(crud.read_all(db, models.Roster.league_id, models.Roster.owner_id)),
        db_txs=set(crud.read_all(db, models.Transaction.transaction_id)),
        db_drafts=set(crud.read_all(db, models.Draft.draft_id))
    )

    await init_players(db, info)

    return info

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
    leagues_json = await sleeper.get_leagues(user_id, info.state.season)
    tasks = []
    for l in leagues_json:
        l_id = l['league_id']
        if l_id not in info.db_leagues:
            info.db_leagues.add(l_id)
            tasks.append(get_league_data(l))
        # else:
        #     logger.info(f'Already stored league {l['name']}')        
    if tasks:
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
        'league_json': league,
        'users_json': users,
        'rosters_json': rosters,
        'trades_json': trades,
        'drafts_json': drafts
    }

async def sync_league_data(db: Session, info: 'Info', league_data: list):
    leagues = []
    users = []
    rosters = []
    transactions = []
    movements = []
    waivers = []
    picks = []
    drafts = []
    for data in league_data:  
        # --- League ---
        l_json = data['league_json']
        l_schema = schemas.SleeperLeague(**l_json)
        leagues.append(models.League(**mappers.league_to_db(l_schema)))

        # --- Users ---
        for u_json in data['users_json']:
            if u_json['user_id'] not in info.db_users:
                u_schema = schemas.SleeperUser(**u_json)
                users.append(models.User(**mappers.schema_to_db(u_schema)))
                info.db_users.add(u_json['user_id'])
                
        # --- Rosters ---
        for r_json in data['rosters_json']:
            if (r_json['league_id'], r_json['owner_id']) not in info.db_rosters:
                r_schema = schemas.SleeperRoster(**r_json)
                rosters.append(models.Roster(**mappers.roster_to_db(r_schema)))
                info.db_rosters.add((r_json['league_id'], r_json['owner_id']))

        # --- Trades ---
        for t_json in data['trades_json']:
            if t_json['type'] == 'trade' and t_json['transaction_id'] not in info.db_txs:
                t_schema = schemas.SleeperTransaction(**t_json)
                t_map, m_map, w_map, p_map = mappers.tx_to_db(t_schema, l_schema)
                transactions.append(models.Transaction(**t_map))
                info.db_txs.add(t_json['transaction_id'])
                movements.extend([models.Movement(**m) for m in m_map])
                waivers.extend([models.WaiverBudget(**w) for w in w_map])
                picks.extend([models.TradedPick(**p) for p in p_map])

        # --- Drafts ---
        for d_json in data['drafts_json']:
            if d_json['draft_id'] not in info.db_drafts:
                d_schema = schemas.SleeperDraft(**d_json)
                drafts.append(models.Draft(**mappers.schema_to_db(d_schema)))
                info.db_drafts.add(d_json['draft_id'])

    db.add_all(leagues)
    db.add_all(users)
    db.add_all(rosters)
    db.add_all(transactions)
    db.add_all(movements)
    db.add_all(waivers)
    db.add_all(picks)
    db.add_all(drafts)

    logger.info(
        f"Queued: {len(leagues)} Leagues, {len(users)} Users, {len(rosters)} Rosters, "
        f"{len(transactions)} Transactions ({len(movements)} Movements), {len(drafts)} Drafts"
    )

async def init_players(db: Session, info: 'Info'):
    state = db.query(models.InternalState).filter_by(key="last_player_map_update").first()
    last_update = None
    if state:
        last_update = datetime.fromisoformat(state.value)    
    one_month_ago = datetime.now() - timedelta(days=30)
    
    if not last_update or last_update < one_month_ago:
        players_json = await sleeper.get_all_players()
        update_count = 0
        players = []
        for p_id, p_json in players_json.items():
            p_schema = schemas.SleeperPlayer(**p_json)
            p_data = mappers.schema_to_db(p_schema) 
            existing = info.player_map.get(p_id)
            if not existing:
                new_p = models.Player(**p_data)
                players.append(new_p)
                info.player_map[p_id] = new_p
            else:
                for key, value in p_data.items():
                    if key != 'player_id':
                        continue
                    setattr(existing, key, value)
                    update_count += 1
        
        db.add_all(players)
        if not state:
            state = models.InternalState(key="last_player_map_update")
            db.add(state)
        state.value = datetime.now().isoformat()
        db.commit()
        logger.info(f"Player Sync: {len(players)} inserted, {update_count} updated.")

    else:
        logger.info(f"Player map is current (Last updated: {last_update.date()})")

async def sync_players(db: Session):
    player_map={p.player_id: p for p in crud.read_all(db, models.Player)}
    players_json = await sleeper.get_all_players()
    update_count = 0
    players = []
    for p_id, p_json in players_json.items():
        p_schema = schemas.SleeperPlayer(**p_json)
        p_data = mappers.schema_to_db(p_schema) 
        existing = player_map.get(p_id)
        if not existing:
            new_p = models.Player(**p_data)
            players.append(new_p)
            player_map[p_id] = new_p
        else:
            for key, value in p_data.items():
                if key != 'player_id':
                    continue
                setattr(existing, key, value)
                update_count += 1

    db.add_all(players)
    state = db.query(models.InternalState).filter_by(key="last_player_map_update").first()
    if not state:
        state = models.InternalState(key="last_player_map_update")
        db.add(state)
    state.value = datetime.now().isoformat()
    db.commit()
    logger.info(f"Player Sync: {len(players)} inserted, {update_count} updated.")