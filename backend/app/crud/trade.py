import logging, asyncio
from collections import defaultdict
from typing import List, Dict
from sqlmodel import select
from sqlalchemy import func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import models
from app.schemas import schemas
from app.crud.league import get_league_map
from app.crud.leaguemate import get_leaguemate_ids
from app.crud.player import get_player_map
from app.crud.user import user_id_lookup

logger = logging.getLogger(__name__)

async def get_user_meta_map(db: AsyncSession) -> Dict[str, dict]:
    """Fetches high-level metadata maps for displaying names and user avatars."""
    stmt = select(
        models.User.user_id, 
        models.User.display_name, 
        models.User.avatar, 
        models.User.is_placeholder
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    return {
        user_id: {
            "name": display_name,
            "avatar": avatar,
            "is_placeholder": is_placeholder,
        }
        for user_id, display_name, avatar, is_placeholder in rows
    }

async def read_trades(db: AsyncSession, lms: list) -> Dict[str, dict]:
    """
    Fetches raw database rows and groups them safely by transaction_id.
    Leverages the new lazy-loaded models and composite database indexes 
    for sub-second data extraction.
    """
    trade_ids_stmt = (
        select(models.Transaction.transaction_id)
        .join(models.Movement, models.Movement.transaction_id == models.Transaction.transaction_id)
        .join(
            models.Roster, 
            and_(
                models.Roster.roster_id == models.Movement.roster_id, 
                models.Roster.league_id == models.Transaction.league_id
            )
        )
        .where(models.Roster.owner_id.in_(lms))
        .distinct()
    )
    result = await db.execute(trade_ids_stmt)
    trade_ids = list(result.scalars().all())

    if not trade_ids:
        return {}

    tasks = [
        db.execute(select(models.Transaction).where(models.Transaction.transaction_id.in_(trade_ids))),
        db.execute(select(models.Movement).where(models.Movement.transaction_id.in_(trade_ids))),
        db.execute(select(models.TradedPick).where(models.TradedPick.transaction_id.in_(trade_ids))),
        db.execute(select(models.WaiverBudget).where(models.WaiverBudget.transaction_id.in_(trade_ids)))
    ]
    
    t_res, m_res, p_res, w_res = await asyncio.gather(*tasks)

    trades_rows = t_res.scalars().unique().all()
    movements_rows = m_res.scalars().unique().all()
    picks_rows = p_res.scalars().unique().all()
    waivers_rows = w_res.scalars().unique().all()

    lm_trades = defaultdict(lambda: {'trade': None, 'movements': [], 'picks': [], 'waivers': []})
    
    for t in trades_rows: 
        lm_trades[t.transaction_id]['trade'] = t
        
    for m in movements_rows: 
        lm_trades[m.transaction_id]['movements'].append(m)
        
    for p in picks_rows: 
        lm_trades[p.transaction_id]['picks'].append(p)
        
    for w in waivers_rows: 
        lm_trades[w.transaction_id]['waivers'].append(w)

    return lm_trades

async def get_trade_signals(db: AsyncSession, username: str) -> List[schemas.DisplayTransaction]:
    """
    Evaluates historical trade records to find high-value cross-league strategies.
    Uses structured milestone logging for stateless engine auditing.
    """

    try:
        main_user_id = await user_id_lookup(db, username)
        logger.info(f"Initiating trade signal calculation matrix for user: {username}")
        lm_ids = await get_leaguemate_ids(db, main_user_id)
        logger.info(f"Context loaded: Identified {len(lm_ids)} unique leaguemates.")

        lm_trades_data = await read_trades(db, lm_ids)
        if not lm_trades_data:
            logger.info("Matrix generation skipped: No relevant trade records found.")
            return []

        total_trades = len(lm_trades_data)
        logger.info(f"Dataset compiled: Processing {total_trades} historical transactions.")

        league_map = await get_league_map(db)
        user_meta = await get_user_meta_map(db)

        trade_league_ids = {tx_data['trade'].league_id for tx_data in lm_trades_data.values() if tx_data['trade']}
        roster_owner_map = defaultdict(dict)
        
        r_stmt = (
            select(models.Roster.league_id, models.Roster.owner_id, models.Roster.roster_id)
            .where(models.Roster.league_id.in_(trade_league_ids))
        )
        r_res = await db.execute(r_stmt)
        roster_rows = r_res.all()
        
        for l_id, o_id, r_id in roster_rows:
            roster_owner_map[l_id][r_id] = o_id

        my_leagues = select(models.Roster.league_id).where(models.Roster.owner_id == main_user_id).scalar_subquery()

        intersect_stmt = (
            select(models.Roster.league_id, models.Roster.owner_id, func.unnest(models.Roster.players))
            .where(models.Roster.league_id.in_(my_leagues))
            .where(or_(models.Roster.owner_id.in_(lm_ids), models.Roster.owner_id == main_user_id))
        )
        int_res = await db.execute(intersect_stmt)
        intersect_query = int_res.all()
        
        player_to_leagues = defaultdict(lambda: defaultdict(set))
        shared_leagues = defaultdict(set)
        for l_id, o_id, p_id in intersect_query:
            player_to_leagues[o_id][p_id].add(l_id)
            if o_id != main_user_id:
                shared_leagues[o_id].add(l_id)

        draft_orders = defaultdict(dict)
        d_res = await db.execute(select(models.Draft.draft_id, models.Draft.season, models.Draft.draft_order))
        raw_drafts = d_res.all()
        
        for d_id, season, d_order in raw_drafts:
            draft_orders[d_id][season] = d_order or {}

        player_map = await get_player_map(db)
        
        final_trades = []
        log_milestone = max(1, total_trades // 10)
        
        logger.info("Starting processing loop execution blocks...")
        
        for idx, (tx_id, tx) in enumerate(lm_trades_data.items(), start=1):
            trade_obj = tx['trade']
            if not trade_obj:
                if idx % log_milestone == 0 or idx == total_trades:
                    logger.info(f"[Task Progress] Evaluated {idx}/{total_trades} records ({(idx / total_trades) * 100:.1f}%)")
                continue
                
            league_id = trade_obj.league_id
            users_dict = defaultdict(lambda: {"adds": [], "drops": []})
            has_signal = False

            for m in tx['movements']:
                user_id = roster_owner_map[league_id].get(m.roster_id)
                p_obj = player_map.get(m.player_id)
                if p_obj:
                    asset_name = f"{p_obj.get('position', '')} {p_obj.get('first_name', '')} {p_obj.get('last_name', '')}".strip()
                else:
                    asset_name = "Unknown Player"
                signal_text = ""

                if m.action == "DROP":
                    shared_with_this_lm = player_to_leagues[user_id][m.player_id].intersection(shared_leagues[user_id])
                    if shared_with_this_lm and user_id != main_user_id:
                        signals = [league_map[lid] for lid in shared_with_this_lm if lid in league_map]
                        signal_text = f"Buy opportunity ({', '.join(signals)})"
                        has_signal = True
                    users_dict[user_id]["drops"].append(schemas.DisplayMovement(name=asset_name, signal=signal_text))

                elif m.action == "ADD":
                    my_ownership = player_to_leagues[main_user_id][m.player_id].intersection(shared_leagues[user_id])
                    if my_ownership and user_id != main_user_id:
                        signals = [league_map[lid] for lid in my_ownership if lid in league_map]
                        signal_text = f"Sell opportunity ({', '.join(signals)})"
                        has_signal = True
                    users_dict[user_id]["adds"].append(schemas.DisplayMovement(name=asset_name, signal=signal_text))

            for p in tx['picks']:
                signal_text = ""
                year = p.season
                round_num = p.round
                draft_id = getattr(p, 'draft_id', None)
                
                user_id = roster_owner_map[league_id].get(p.new_roster_id)
                old_user_id = roster_owner_map[league_id].get(p.old_roster_id)
                og_user_id = roster_owner_map[league_id].get(p.og_roster_id)
                
                try:
                    draft_order = draft_orders[draft_id][year]
                    pick_slot = draft_order[og_user_id]
                    asset = f"{year} Pick {round_num}.{pick_slot:02d}"
                except:
                    asset = f"{year} Round {round_num}"
                    
                if user_id not in users_dict:
                    users_dict[user_id] = {"adds": [], "drops": []}
                users_dict[user_id]["adds"].append(schemas.DisplayMovement(name=asset, signal=signal_text))
                
                if old_user_id not in users_dict:
                    users_dict[old_user_id] = {"adds": [], "drops": []}
                users_dict[old_user_id]["drops"].append(schemas.DisplayMovement(name=asset, signal=signal_text))

            for w in tx['waivers']:
                signal_text = ""
                user_id = roster_owner_map[league_id].get(w.receiver)
                old_user_id = roster_owner_map[league_id].get(w.sender)
                asset = f"${w.amount}"
                
                if user_id not in users_dict:
                    users_dict[user_id] = {"adds": [], "drops": []}
                users_dict[user_id]["adds"].append(schemas.DisplayMovement(name=asset, signal=signal_text))
                
                if old_user_id not in users_dict:
                    users_dict[old_user_id] = {"adds": [], "drops": []}
                users_dict[old_user_id]["drops"].append(schemas.DisplayMovement(name=asset, signal=signal_text))

            if has_signal:
                ui_users = []
                for u_id, data in users_dict.items():
                    meta = user_meta.get(u_id, {"name": "Unknown", "avatar": None, "is_placeholder": False})
                    ui_users.append(schemas.DisplayUser(
                        display_name=meta["name"],
                        avatar=meta["avatar"],
                        is_placeholder=meta["is_placeholder"],
                        adds=data["adds"],
                        drops=data["drops"]
                    ))
                
                final_trades.append(schemas.DisplayTransaction(
                    transaction_id=tx_id,
                    time_ms=trade_obj.time_ms or 0,
                    league_name=league_map.get(league_id, "Unknown League"),
                    users=ui_users
                ))

            if idx % log_milestone == 0 or idx == total_trades:
                logger.info(f"[Task Progress] Evaluated {idx}/{total_trades} records ({(idx / total_trades) * 100:.1f}%)")
                
        logger.info(f"Calculation complete. Identified {len(final_trades)} actionable trade cross-signals.")
        return sorted(final_trades, key=lambda x: x.time_ms, reverse=True)
                
    except Exception as e:
        logger.error(f"Execution runtime error in signal parsing engine: {str(e)}", exc_info=True)
        raise e