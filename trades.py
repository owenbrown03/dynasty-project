from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session, noload, selectinload, joinedload, subqueryload
from models import Info
from collections import defaultdict
import models, schemas, logging

logger = logging.getLogger(__name__)

async def trade_signals(db: Session, info: Info):
    lm_trades = await read_trades(db, info)
    
    # PUT IN A HELPER
    raw_leagues = db.execute(
        select(
            models.League.league_id, 
            models.League.name
        )
        .distinct()
    ).all()

    league_names = {}
    for league_id, name in raw_leagues:
        league_names[league_id] = name

    raw_users = db.execute(
        select(
            models.User.user_id, 
            models.User.display_name,
            models.User.avatar
        )
        .distinct()
    ).all()

    db_users = defaultdict(lambda: {
        'username': '',
        'avatar': ''
    })
    for user_id, display_name, avatar in raw_users:
        db_users[user_id]['username'] = display_name
        db_users[user_id]['avatar'] = avatar
    
    raw_players = db.execute(
        select(
            models.Player.player_id,
            models.Player.first_name,
            models.Player.last_name
        )
        .distinct()
    ).all()

    player_names = {}
    for player_id, first_name, last_name in raw_players:
        player_names[player_id] = f"{first_name} {last_name}"
    # END OF PUT IN A HELPER

    lm_leagues = (
        select(models.Roster.league_id)
        .where(models.Roster.owner_id.in_(info.lms))
        .scalar_subquery()
    )

    all_rosters = db.execute(
        select(
            models.Roster.league_id, 
            models.Roster.owner_id, 
            models.Roster.roster_id
        )
        .where(models.Roster.league_id.in_(lm_leagues))
    ).all()

    user_ids = defaultdict(lambda: defaultdict(str))
    for league_id, owner_id, roster_id in all_rosters:
            user_ids[league_id][roster_id] = owner_id

    my_leagues = (
        select(models.Roster.league_id)
        .where(models.Roster.owner_id == info.main_user.user_id)
        .scalar_subquery()
    )

    shared_rosters = db.execute(
        select(
            models.Roster.league_id, 
            models.Roster.owner_id, 
            func.unnest(models.Roster.players)
        )
        .where(models.Roster.league_id.in_(my_leagues))
        .where(
            or_(
                models.Roster.owner_id.in_(info.lms),
                models.Roster.owner_id == info.main_user.user_id
            )
        )
    ).all()

    player_to_leagues = defaultdict(lambda: defaultdict(set))
    shared_leagues = defaultdict(set)
    for league_id, owner_id, player_id in shared_rosters:
            player_to_leagues[owner_id][player_id].add(league_id)
            shared_leagues[owner_id].add(league_id)
    
    trades: list[schemas.Transaction] = []
    for id, tx in lm_trades.items():
        league_id = tx['trade']['league_id']
        users_dict = {}
        signals = []
        for m in tx['movements']:
            signal_text = ""
            user_id = user_ids[league_id][m['roster_id']]
            player = player_names.get(m['player_id'], "Unknown Player")
            if user_id not in users_dict:
                users_dict[user_id] = {"adds": [], "drops": []}
            if m['action'] == "DROP": # buy? lm dropped player and intersection between lm having player in a league with me
                #buys = player_to_leagues[user_id][m['player_id']].intersection(shared_leagues[user_id])
                signals = {league_names[lid] for lid in player_to_leagues[user_id][m['player_id']].intersection(shared_leagues[user_id]) if lid in league_names}
                if signals: signal_text = f"Buy opportunity ({', '.join(signals)})"
                users_dict[user_id]["drops"].append(schemas.Movement(
                    name=player,
                    signal=signal_text
                ))
            elif m['action'] == "ADD": # sell? lm added player and intersection between me having player in a league with lm 
                #sells = player_to_leagues[info.main_user.user_id][m['player_id']].intersection(shared_leagues[user_id])
                signals = {league_names[lid] for lid in player_to_leagues[info.main_user.user_id][m['player_id']].intersection(shared_leagues[user_id]) if lid in league_names}
                if signals: signal_text = f"Sell opportunity ({', '.join(signals)})"
                users_dict[user_id]["adds"].append(schemas.Movement(
                    name=player,
                    signal=signal_text
                ))
        if signal_text:
            users = []
            for user_id, data in users_dict.items():
                users.append(schemas.User(
                    display_name=db_users[user_id]['username'],
                    avatar=db_users[user_id]['avatar'],
                    adds=data["adds"],
                    drops=data["drops"]
                ))
            trades.append(schemas.Transaction(
                    transaction_id=id,
                    time_ms=tx['trade']['time_ms'],
                    league_name=league_names[tx['trade']['league_id']],
                    users=users
            ))
    return trades 

async def read_trades(db: Session, info: Info):

    trade_ids = db.execute(
        select(models.Transaction.transaction_id)
        .join(models.Movement)
        .join(models.Roster, 
            (models.Roster.roster_id == models.Movement.roster_id) & 
            (models.Roster.league_id == models.Transaction.league_id))
        .filter(models.Roster.owner_id.in_(info.lms))
        .distinct()
    ).scalars().all()

    raw_trades = db.execute(
        select(
            models.Transaction.transaction_id,
            models.Transaction.time_ms,
            models.Transaction.league_id
        ).filter(models.Transaction.transaction_id.in_(trade_ids))
    ).mappings().all()

    raw_movements = db.execute(
        select(
            models.Movement.transaction_id,
            models.Movement.player_id,
            models.Movement.roster_id,
            models.Movement.action
        ).filter(models.Movement.transaction_id.in_(trade_ids))
    ).mappings().all()

    raw_waiver = db.execute(
        select(
            models.WaiverBudget.transaction_id,
            models.WaiverBudget.sender,
            models.WaiverBudget.receiver,
            models.WaiverBudget.amount
        ).filter(models.WaiverBudget.transaction_id.in_(trade_ids))
    ).mappings().all()

    raw_picks = db.execute(
        select(
            models.TradedPick.transaction_id,
            models.TradedPick.season,
            models.TradedPick.round,
            models.TradedPick.new_owner_id,
            models.TradedPick.old_owner_id
        ).filter(models.TradedPick.transaction_id.in_(trade_ids))
    ).mappings().all()

    lm_trades = defaultdict(lambda: {"trade": {}, "movements": [], "picks": [], "waivers": []})

    for t in raw_trades:
        lm_trades[t['transaction_id']]["trade"] = t
    for m in raw_movements:
        lm_trades[m['transaction_id']]["movements"].append(m)
    for p in raw_picks:
        lm_trades[p['transaction_id']]["picks"].append(p)
    for w in raw_waiver:
        lm_trades[w['transaction_id']]["waivers"].append(w)

    return lm_trades