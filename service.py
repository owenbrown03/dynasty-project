from sqlalchemy.orm import Session
import sleeper, schemas, models, crud, mappers

async def sync_user_data(db: Session, username: str):
    user = schemas.SleeperUser(**await sleeper.get_username_details(username))
    crud.sync(db, models.User(**user.model_dump()))
    state = schemas.NFLState(**await sleeper.get_NFL_state())
    #leagues = [schemas.SleeperLeague(**l) for l in await sleeper.get_leagues(user.user_id, state.season)]
    leaguesJSON = await sleeper.get_leagues(user.user_id, state.season)
    leauge_ct = roster_ct = trade_ct = draft_ct = 0
    for l in leaguesJSON:
        league = schemas.SleeperLeague(**l)
        crud.sync(db, models.League(**mappers.league_to_db(league)))
        leauge_ct += 1
        roster_ct += await sync_user_rosters(db, league, user)
        trade_ct += await sync_league_trades(db, league)
        draft_ct += await sync_league_drafts(db, league)
    return leauge_ct, roster_ct, trade_ct, draft_ct

async def sync_user_rosters(db: Session, league: schemas.SleeperLeague, user: schemas.SleeperUser):
    #rosters = [schemas.SleeperRoster(**r) for r in await sleeper.get_rosters(league.league_id)]
    rostersJSON = await sleeper.get_rosters(league.league_id)
    roster_ct = 0
    #crud.sync(db, models.Roster(**mappers.roster_to_db(next((r for r in rosters if r.owner_id == user.user_id), None))))
    for r in rostersJSON:
        if r.get('owner_id') == user.user_id:
            roster = schemas.SleeperRoster(**r)
            crud.sync(db, models.Roster(**mappers.roster_to_db(roster)))
            roster_ct += 1
    return roster_ct

async def sync_league_trades(db: Session, league: schemas.SleeperLeague): # stores all trades in users leagues
    #txs = [schemas.SleeperTransaction(**t) for t in await sleeper.get_transactions(league.league_id, 1)]
    txsJSON = await sleeper.get_transactions(league.league_id, 1) # NEED TO UPDATE TO DO ALL WEEKS    
    trade_ct = 0
    for t in txsJSON:
        if t.get('type') == "trade":
            trade = schemas.SleeperTransaction(**t)
            transaction, movements, waivers, picks = mappers.tx_to_db(trade, league)
            crud.sync(db, models.Transaction(**transaction))
            trade_ct += 1
            for m in movements:
                crud.sync(db, models.Movement(**m))
            for w in waivers:
                crud.sync(db, models.WaiverBudget(**w))
            for p in picks:
                crud.sync(db, models.TradedPick(**p))
    return trade_ct

async def sync_league_drafts(db: Session, league: schemas.SleeperLeague): # stores all drafts in users leagues
    #drafts = [schemas.SleeperDraft(**d) for d in await sleeper.get_drafts_league(league.league_id)]
    lgdraftJSON = await sleeper.get_drafts_league(league.league_id)
    draft_ct = 0
    for ld in lgdraftJSON:
        lgdraft = schemas.SleeperDraft(**ld)
        #new_draft = [schemas.SleeperDraft(**d) for d in await sleeper.get_draft(draft.draft_id)]
        draftJSON = await sleeper.get_draft(lgdraft.draft_id)
        draft = schemas.SleeperDraft(**draftJSON)
        crud.sync(db, models.Draft(**mappers.schema_to_db(draft)))
        draft_ct += 1
    return draft_ct