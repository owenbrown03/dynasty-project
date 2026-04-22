from sqlalchemy.orm import Session
import sleeper, schemas, models, crud, mappers

async def sync_user_leagues(db: Session, username: str):
    return username

async def sync_user_leagues(db: Session, username: str):
    user = schemas.SleeperUser(**await sleeper.get_username_details(username))
    state = schemas.NFLState(**await sleeper.get_NFL_state())
    leagues = [schemas.SleeperLeague(**l) for l in await sleeper.get_leagues(user.user_id, state.season)]
    for league in leagues:
        crud.sync(db, models.League(**mappers.league_to_db(league)))
    return leagues

async def sync_user_rosters(db: Session, username: str):
    user = schemas.SleeperUser(**await sleeper.get_username_details(username))
    crud.sync(db, models.User(**user.model_dump()))
    state = schemas.NFLState(**await sleeper.get_NFL_state())
    leagues = [schemas.SleeperLeague(**l) for l in await sleeper.get_leagues(user.user_id, state.season)]
    for league in leagues:
        crud.sync(db, models.League(**mappers.league_to_db(league)))
        rosters = [schemas.SleeperRoster(**r) for r in await sleeper.get_rosters(league.league_id)]
        crud.sync(db, models.Roster(**mappers.roster_to_db(next((r for r in rosters if r.owner_id == user.user_id), None))))
    return leagues, rosters

async def sync_league_trades(db: Session, username: str): # stores all trades in users leagues
    user = schemas.SleeperUser(**await sleeper.get_username_details(username))
    state = schemas.NFLState(**await sleeper.get_NFL_state())
    leagues = [schemas.SleeperLeague(**l) for l in await sleeper.get_leagues(user.user_id, state.season)]
    for league in leagues:
        crud.sync(db, models.League(**mappers.league_to_db(league)))
        txs = [schemas.SleeperTransaction(**t) for t in await sleeper.get_transactions(league.league_id, 1)] # NEED TO UPDATE TO DO ALL WEEKS
        print(f"league: {league.league_id} week: {state.week} transactions: {len(txs)}")
        for trade in [t for t in txs if t.type == "trade"]:
            transaction, movements, waivers, picks = mappers.tx_to_db(trade, league)
            crud.sync(db, models.Transaction(**transaction))
            for m in movements:
                crud.sync(db, models.Movement(**m))
            for w in waivers:
                crud.sync(db, models.WaiverBudget(**w))
            for p in picks:
                crud.sync(db, models.TradedPick(**p))
    return leagues, txs

async def sync_league_drafts(db: Session, username: str): # stores all drafts in users leagues
    user = schemas.SleeperUser(**await sleeper.get_username_details(username))
    state = schemas.NFLState(**await sleeper.get_NFL_state())
    leagues = [schemas.SleeperLeague(**l) for l in await sleeper.get_leagues(user.user_id, state.season)]
    for league in leagues:
        crud.sync(db, models.League(**mappers.league_to_db(league)))
        drafts = [schemas.SleeperDraft(**d) for d in await sleeper.get_drafts_league(league.league_id)]
        for draft in drafts:
            new_draft = [schemas.SleeperDraft(**d) for d in await sleeper.get_draft(draft.draft_id)]
            crud.sync(db, models.Draft(**new_draft.model_dump()))
    return leagues, drafts