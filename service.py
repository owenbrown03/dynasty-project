from sqlalchemy.orm import Session
import asyncio, logging, sleeper, schemas, models, crud, mappers

logger = logging.getLogger(__name__)

async def create_user_data(db: Session, username: str):
    user = schemas.SleeperUser(**await sleeper.get_username_details(username))
    await create_user(db, user)
    state = schemas.NFLState(**await sleeper.get_NFL_state())
    db_leagues = set(crud.read_all(db, models.League.league_id))
    leaguesJSON = await sleeper.get_leagues(user.user_id, state.season)
    freshJSON = [l for l in leaguesJSON if l['league_id'] not in db_leagues]
    if not freshJSON:
        logger.info("Everything is already up to date.")
        return 0
    tasks = [get_league_data(l) for l in freshJSON]
    league_data = await asyncio.gather(*tasks)
    await sync_league_data(db, league_data)

async def get_league_data(league: dict):
    l_id = league['league_id']
    users, rosters, trades, drafts = await asyncio.gather(
        sleeper.get_users(l_id),
        sleeper.get_rosters(l_id),
        sleeper.get_transactions(l_id, 1), # NEED TO UPDATE TO DO ALL WEEKS
        sleeper.get_drafts_league(l_id)
    )
    return {
        "leagueJSON": league,
        "usersJSON": users,
        "rostersJSON": rosters,
        "tradesJSON": trades,
        "draftsJSON": drafts
    }

async def sync_league_data(db: Session, league_data: list):
    db_users = crud.read_all(db, models.User.user_id)
    db_rosters = set(crud.read_all(db, models.Roster.roster_id, models.Roster.owner_id))
    db_txs = set(crud.read_all(db, models.Transaction.transaction_id))
    db_drafts = set(crud.read_all(db, models.Draft.draft_id))
    try:
        for data in league_data:  
            #league
            l_schema = schemas.SleeperLeague(**data['leagueJSON'])
            l_model = models.League(**mappers.league_to_db(l_schema))
            db.add(l_model)

            #users
            for u_json in data['usersJSON']:
                if u_json["user_id"] not in db_users:
                    u_schema = schemas.SleeperUser(**u_json)
                    db.add(models.User(**mappers.schema_to_db(u_schema)))
                    db_users.add(u_json["user_id"])
        
            #rosters
            for r_json in data['rostersJSON']:
                if (r_json["roster_id"], r_json["owner_id"]) not in db_rosters:
                    r_schema = schemas.SleeperRoster(**r_json)
                    db.add(models.Roster(**mappers.roster_to_db(r_schema)))
                    db_rosters.add((r_json["roster_id"], r_json["owner_id"]))
            
            #trades
            for t_json in data['tradesJSON']:
                if t_json['type'] == "trade" and t_json['transaction_id'] not in db_txs:
                    t_schema = schemas.SleeperTransaction(**t_json)
                    t_map, m_map, w_map, p_map = mappers.tx_to_db(t_schema, l_schema)
                    t_model = models.Transaction(**t_map)
                    m_models = [models.Movement(**m) for m in m_map]
                    w_models = [models.WaiverBudget(**w) for w in w_map]
                    p_models = [models.TradedPick(**p) for p in p_map]
                    db.add(t_model)
                    db_txs.add(t_json['transaction_id'])
                    db.add_all(m_models)
                    db.add_all(w_models)
                    db.add_all(p_models)
            
            #drafts
            for d_json in data['draftsJSON']:
                if d_json['draft_id'] not in db_drafts:
                    d_schema = schemas.SleeperDraft(**d_json)
                    db.add(models.Draft(**mappers.schema_to_db(d_schema)))
                    db_drafts.add(d_json['draft_id'])

        db.commit()
        logger.info(f"Successfully committed {len(league_data)} leagues to the database.")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save sync results: {e}", exc_info=True)
        raise
        
async def create_user(db: Session, user: schemas.SleeperUser):
    db.add(models.User(**mappers.schema_to_db(user)))
    db.flush()
    #crud.upsert(db, models.User(**mappers.schema_to_db(user)))

async def create_league_lm(db: Session, league: schemas.SleeperLeague, ):
    usersJSON = await sleeper.get_users(league.league_id)
    user_ct = 0
    for u in usersJSON:
        user = schemas.SleeperUser(**u)
        await create_user(db, user)
        user_ct += 1
    return user_ct

async def create_user_leagues(db: Session, user_id: str, season: str):
    db_lgs = {row[0] for row in crud.read_all(db, models.League.league_id)}
    leaguesJSON = await sleeper.get_leagues(user_id, season)
    leauge_ct = 0
    for l in leaguesJSON:
        if l['league_id'] not in db_lgs:
            league = schemas.SleeperLeague(**l)
            crud.create(db, models.League(**mappers.league_to_db(league)))
            leauge_ct += 1
    return leauge_ct

async def create_user_rosters(db: Session, user_id: str, season: str):
    db_lgs = {row[0] for row in crud.read_all(db, models.League.league_id)}
    leaguesJSON = await sleeper.get_leagues(user_id, season)
    roster_ct = 0
    for l in leaguesJSON:
        if l['league_id'] not in db_lgs:
            league = schemas.SleeperLeague(**l)
            crud.create(db, models.League(**mappers.league_to_db(league)))
            roster_ct += await create_user_roster(db, league, user_id)
    return roster_ct

async def create_league_rosters(db: Session, league: schemas.SleeperLeague):
    rostersJSON = await sleeper.get_rosters(league.league_id)
    roster_ct = 0
    for r in rostersJSON:
        roster = schemas.SleeperRoster(**r)
        crud.create(db, models.Roster(**mappers.roster_to_db(roster)))
        roster_ct += 1
    return roster_ct

async def create_user_roster(db: Session, league: schemas.SleeperLeague, user_id: str):
    rostersJSON = await sleeper.get_rosters(league.league_id)
    roster_ct = 0
    for r in rostersJSON:
        if r['owner_id'] == user_id:
            roster = schemas.SleeperRoster(**r)
            crud.create(db, models.Roster(**mappers.roster_to_db(roster)))
            roster_ct += 1
    return roster_ct

async def create_league_trades(db: Session, league: schemas.SleeperLeague): # stores all trades in users leagues
    txsJSON = await sleeper.get_transactions(league.league_id, 1) # NEED TO UPDATE TO DO ALL WEEKS    
    trade_ct = 0
    for t in txsJSON:
        if t['type'] == "trade":
            trade = schemas.SleeperTransaction(**t)
            transaction, movements, waivers, picks = mappers.tx_to_db(trade, league)
            crud.create(db, models.Transaction(**transaction))
            trade_ct += 1
            for m in movements:
                crud.create(db, models.Movement(**m))
            for w in waivers:
                crud.create(db, models.WaiverBudget(**w))
            for p in picks:
                crud.create(db, models.TradedPick(**p))
    return trade_ct

async def create_league_drafts(db: Session, league: schemas.SleeperLeague): # stores all drafts in users leagues
    lgdraftJSON = await sleeper.get_drafts_league(league.league_id)
    draft_ct = 0
    for ld in lgdraftJSON:
        lgdraft = schemas.SleeperDraft(**ld)
        draftJSON = await sleeper.get_draft(lgdraft.draft_id)
        draft = schemas.SleeperDraft(**draftJSON)
        crud.create(db, models.Draft(**mappers.schema_to_db(draft)))
        draft_ct += 1
    return draft_ct

async def create_lm_lgs(db: Session): # stores all leaguemate's leagues in users leagues
    state = schemas.NFLState(**await sleeper.get_NFL_state())
    db_users = {row[0] for row in crud.read_all(db, models.User.user_id)}
    for u in db_users:
        await create_user_leagues(db, u, state.season)

async def create_lm_rosters(db: Session): # stores all leaguemate's leagues in users leagues
    state = schemas.NFLState(**await sleeper.get_NFL_state())
    db_users = {row[0] for row in crud.read_all(db, models.User.user_id)}
    for u in db_users:
        await create_user_rosters(db, u, state.season)