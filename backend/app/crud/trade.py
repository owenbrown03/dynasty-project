from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
from collections import defaultdict
import logging

from app.models import models
from app.schemas import schemas
from app.crud.base import get_league_map, get_user_meta_map
from app.crud.player import get_player_map
from app.crud.leaguemate import get_leaguemates

logger = logging.getLogger(__name__)

async def trade_signals(db: Session, main_user_id: str):

    lms = get_leaguemates(db, main_user_id)
    lm_trades_data = await read_trades(db, lms)
    if not lm_trades_data:
        return []

    league_map = get_league_map(db)
    user_meta = get_user_meta_map(db)

    trade_league_ids = {t['trade']['league_id'] for t in lm_trades_data.values()}
    roster_owner_map = defaultdict(dict)
    roster_rows = db.execute(
        select(models.Roster.league_id, models.Roster.owner_id, models.Roster.roster_id)
        .where(models.Roster.league_id.in_(trade_league_ids))
    ).all()
    for l_id, o_id, r_id in roster_rows:
        roster_owner_map[l_id][r_id] = o_id

    my_leagues = select(models.Roster.league_id).where(models.Roster.owner_id == main_user_id).scalar_subquery()
    intersect_query = db.execute(
        select(models.Roster.league_id, models.Roster.owner_id, func.unnest(models.Roster.players))
        .where(models.Roster.league_id.in_(my_leagues))
        .where(or_(models.Roster.owner_id.in_(lms), models.Roster.owner_id == main_user_id))
    ).all()
    player_to_leagues = defaultdict(lambda: defaultdict(set))
    shared_leagues = defaultdict(set)
    for l_id, o_id, p_id in intersect_query:
        player_to_leagues[o_id][p_id].add(l_id)
        if o_id != main_user_id:
            shared_leagues[o_id].add(l_id)

    draft_orders = defaultdict(dict)
    raw_drafts = db.execute(select(models.Draft.draft_id, models.Draft.season, models.Draft.draft_order)).all()
    for d_id, season, d_order in raw_drafts:
        draft_orders[d_id][season] = d_order

    player_map = get_player_map(db)
    final_trades = []    
    for tx_id, tx in lm_trades_data.items():
        league_id = tx['trade']['league_id']
        users_dict = defaultdict(lambda: {"adds": [], "drops": []})
        has_signal = False

        for m in tx['movements']:
            user_id = roster_owner_map[league_id].get(m['roster_id'])
            p_obj = player_map.get(m['player_id'])
            asset_name = f"{p_obj.position} {p_obj.first_name} {p_obj.last_name}" if p_obj else "Unknown Player"
            signal_text = ""

            if m['action'] == "DROP":
                # BUY SIGNAL: LM dropped a player you also own in a different shared league
                shared_with_this_lm = player_to_leagues[user_id][m['player_id']].intersection(shared_leagues[user_id])
                if shared_with_this_lm:
                    signals = [league_map[lid] for lid in shared_with_this_lm if lid in league_map]
                    signal_text = f"Buy opportunity ({', '.join(signals)})"
                    has_signal = True
                users_dict[user_id]["drops"].append(schemas.Movement(name=asset_name, signal=signal_text))

            elif m['action'] == "ADD":
                # SELL SIGNAL: LM added a player you own in a league with them
                my_ownership = player_to_leagues[main_user_id][m['player_id']].intersection(shared_leagues[user_id])
                if my_ownership:
                    signals = [league_map[lid] for lid in my_ownership if lid in league_map]
                    signal_text = f"Sell opportunity ({', '.join(signals)})"
                    has_signal = True
                users_dict[user_id]["adds"].append(schemas.Movement(name=asset_name, signal=signal_text))

        for p in tx['picks']:
            signal_text = ""
            year = p['season']
            round = p['round']
            draft_id = p['draft_id']
            user_id = roster_owner_map[league_id].get(p['new_roster_id'])
            old_user_id = roster_owner_map[league_id].get(p['old_roster_id'])
            og_user_id = roster_owner_map[league_id].get(p['og_roster_id'])
            try:
                draft_order = draft_orders[draft_id][year]
                pick_slot = draft_order[og_user_id]
                asset = f"{year} Pick {round}.{pick_slot:02d}"
            except:
                asset = f"{year} Round {round}"
            if user_id not in users_dict:
                users_dict[user_id] = {"adds": [], "drops": []}
            users_dict[user_id]["adds"].append(schemas.Movement(
                    name=asset,
                    signal=signal_text
            ))
            if old_user_id not in users_dict:
                users_dict[old_user_id] = {"adds": [], "drops": []}
            users_dict[old_user_id]["drops"].append(schemas.Movement(
                    name=asset,
                    signal=signal_text
            ))

        for w in tx['waivers']:
            signal_text = ""
            user_id = roster_owner_map[league_id].get(w['receiver'])
            old_user_id = roster_owner_map[league_id].get(w['sender'])
            asset = f"${w['amount']}"
            if user_id not in users_dict:
                users_dict[user_id] = {"adds": [], "drops": []}
            users_dict[user_id]["adds"].append(schemas.Movement(
                    name=asset,
                    signal=signal_text
            ))
            if old_user_id not in users_dict:
                users_dict[old_user_id] = {"adds": [], "drops": []}
            users_dict[old_user_id]["drops"].append(schemas.Movement(
                    name=asset,
                    signal=signal_text
            ))

        if has_signal:
            ui_users = []
            for u_id, data in users_dict.items():
                meta = user_meta.get(u_id, {"name": "Unknown", "avatar": None})
                ui_users.append(schemas.User(
                    display_name=meta["name"],
                    avatar=meta["avatar"],
                    adds=data["adds"],
                    drops=data["drops"]
                ))
            
            final_trades.append(schemas.Transaction(
                transaction_id=tx_id,
                time_ms=tx['trade']['time_ms'],
                league_name=league_map.get(league_id, "Unknown League"),
                users=ui_users
            ))

    return sorted(final_trades, key=lambda x: x.time_ms, reverse=True)

async def read_trades(db: Session, lms: list):
    trade_ids = db.execute(
        select(models.Transaction.transaction_id)
        .join(models.Movement)
        .join(models.Roster, (models.Roster.roster_id == models.Movement.roster_id) & 
                            (models.Roster.league_id == models.Transaction.league_id))
        .filter(models.Roster.owner_id.in_(lms))
        .distinct()
    ).scalars().all()

    if not trade_ids:
        return {}

    trades = db.execute(select(models.Transaction).filter(models.Transaction.transaction_id.in_(trade_ids))).mappings().all()
    movements = db.execute(select(models.Movement).filter(models.Movement.transaction_id.in_(trade_ids))).mappings().all()
    picks = db.execute(select(models.TradedPick).filter(models.TradedPick.transaction_id.in_(trade_ids))).mappings().all()
    waivers = db.execute(select(models.WaiverBudget).filter(models.WaiverBudget.transaction_id.in_(trade_ids))).mappings().all()

    lm_trades = defaultdict(lambda: {'trade': {}, 'movements': [], 'picks': [], 'waivers': []})
    for t in trades: lm_trades[t['transaction_id']]['trade'] = t
    for m in movements: lm_trades[m['transaction_id']]['movements'].append(m)
    for p in picks: lm_trades[p['transaction_id']]['picks'].append(p)
    for w in waivers: lm_trades[w['transaction_id']]['waivers'].append(w)

    return lm_trades