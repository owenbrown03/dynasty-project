from sqlalchemy.orm import Session
import sleeper, schemas, models, crud, mappers

async def create_user_data(db: Session, username: str):
    user = schemas.SleeperUser(**await sleeper.get_username_details(username))
    await create_user(db, user)
    state = schemas.NFLState(**await sleeper.get_NFL_state())
    db_lgs = {row[0] for row in crud.read_all(db, models.League.league_id)}
    leaguesJSON = await sleeper.get_leagues(user.user_id, state.season)
    user_ct = leauge_ct = roster_ct = trade_ct = draft_ct = 0
    for l in leaguesJSON:
        if l['league_id'] not in db_lgs:
            league = schemas.SleeperLeague(**l)
            crud.create(db, models.League(**mappers.league_to_db(league)))
            leauge_ct += 1
            user_ct += await create_user_lm(db, league)
            # print(f"DEBUG: Successfully committed {user_ct} users.")
            # check = db.query(models.User).filter_by(user_id="655830556696727552").first()
            # if check:
            #     print("DEBUG: The missing user IS in the DB. This is a ghost error.")
            # else:
            #     print("DEBUG: The missing user is NOT in the DB. create_user_lm skipped them.")
            roster_ct += await create_league_rosters(db, league)
            trade_ct += await create_league_trades(db, league)
            draft_ct += await create_league_drafts(db, league)
    return user_ct, leauge_ct, roster_ct, trade_ct, draft_ct

async def create_user(db: Session, user: schemas.SleeperUser):
    crud.create(db, models.User(**mappers.schema_to_db(user)))

async def create_user_lm(db: Session, league: schemas.SleeperLeague, ):
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
    return leauge_ct

async def create_league_rosters(db: Session, league: schemas.SleeperLeague):
    rostersJSON = await sleeper.get_rosters(league.league_id)
    roster_ct = 0
    for r in rostersJSON:
        roster = schemas.SleeperRoster(**r)
        crud.create(db, models.Roster(**mappers.roster_to_db(roster)))
        roster_ct += 1
    return roster_ct

async def create_user_rosters(db: Session, league: schemas.SleeperLeague, user: schemas.SleeperUser):
    rostersJSON = await sleeper.get_rosters(league.league_id)
    roster_ct = 0
    for r in rostersJSON:
        if r['owner_id'] == user.user_id:
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