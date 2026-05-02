from sqlalchemy import select
from sqlalchemy.orm import Session, noload, selectinload, joinedload, subqueryload
from models import Info
from collections import defaultdict
import models

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

    lm_trades = defaultdict(lambda: {"trades": [], "movements": [], "picks": [], "waivers": []})

    for t in raw_trades:
        lm_trades[t['transaction_id']]["trades"].append(t)
    for m in raw_movements:
        lm_trades[m['transaction_id']]["movements"].append(m)
    for p in raw_picks:
        lm_trades[p['transaction_id']]["picks"].append(p)
    for w in raw_waiver:
        lm_trades[w['transaction_id']]["waivers"].append(w)

    return lm_trades