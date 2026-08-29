from __future__ import annotations

import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.sleeper.roster import get_all_rosters_by_league
from app.crud.sleeper.user import get_user_names_by_id
from app.integrations.sleeper.client import SleeperClient
from app.integrations.sleeper.exceptions import SleeperError
from app.models.db.sleeper import api as model
from app.models.db.sleeper.connection import SleeperConnection
from app.schemas.trades import BulkTradeOfferRequest

logger = logging.getLogger(__name__)

_DM_PROPOSED_STATUS = "proposed"

_ATTACHMENT_KEYS = [
    "status",
    "transaction_id",
    "league_id",
    "transactions_by_roster",
    "users_in_league_map",
]


def _extract_dm_id(payload) -> str | None:
    """Sleeper returns the DM either as a single object or a list."""
    if not payload:
        return None

    if isinstance(payload, list):
        for entry in payload:
            dm_id = _extract_dm_id(entry)
            if dm_id:
                return dm_id
        return None

    if isinstance(payload, dict):
        return (
            payload.get("dm_id")
            or payload.get("create_dm", {}).get("dm_id")
            or payload.get("get_dm_by_members", {}).get("dm_id")
        )

    return None


async def send_trade_dm_to_manager(
    sleeper: SleeperClient,
    *,
    transaction_id: str,
    league_id: str,
    league_name: str,
    sender_display_name: str,
    manager_user_id: str,
    transactions_by_roster: dict,
    users_in_league_map: dict,
) -> dict:
    """Ensure a 1:1 DM channel with the manager exists, then post a message
    announcing the proposed trade with the trade card embedded."""
    if not manager_user_id or not transaction_id:
        logger.warning(
            "Skipping trade DM: manager_user_id=%r transaction_id=%r",
            manager_user_id,
            transaction_id,
        )
        return {}

    # 1. Resolve the existing DM channel, creating it if needed.
    try:
        existing = await sleeper.write.get_dm_by_members([manager_user_id])
    except SleeperError as exc:
        logger.info(
            "get_dm_by_members failed (falling back to create_dm): %s",
            exc,
        )
        existing = []

    dm_id = _extract_dm_id(existing)

    if not dm_id:
        created = await sleeper.write.create_dm([manager_user_id])
        dm_id = _extract_dm_id(created)

    if not dm_id:
        raise SleeperError(
            "Could not open a DM with the manager to share this trade."
        )

    # 2. Post the trade card message.
    text = (
        f"<@{sender_display_name}> has proposed a trade"
        f" in {league_name}"
    )

    return await sleeper.write.create_message(
        parent_id=dm_id,
        parent_type="dm",
        text=text,
        attachment_type="trade_dm",
        k_attachment_data=_ATTACHMENT_KEYS,
        v_attachment_data=[
            _DM_PROPOSED_STATUS,
            str(transaction_id),
            str(league_id),
            json.dumps(transactions_by_roster),
            json.dumps(users_in_league_map),
        ],
    )


async def maybe_send_trade_dm(
    db: AsyncSession,
    sleeper: SleeperClient,
    connection: SleeperConnection,
    *,
    offer: BulkTradeOfferRequest,
    transaction_id: str | None,
) -> None:
    """Send the trade DM to the counterparty manager when `offer.send_dm` is
    set and the trade was proposed successfully. Non-fatal on failure — a DM
    hiccup must never fail an already-accepted trade."""
    if not offer.send_dm:
        return

    if not transaction_id:
        logger.warning(
            "Trade DM requested but no transaction_id returned "
            "for league=%s — skipping.",
            offer.league_id,
        )
        return

    sender_user_id = connection.sleeper_user_id
    sender_names = await get_user_names_by_id(
        db=db,
        user_ids={sender_user_id} if sender_user_id else set(),
    )
    sender_display_name = (
        sender_names.get(sender_user_id)
        if sender_user_id
        else None
    ) or connection.sleeper_username or "a manager"

    league_row = await db.get(
        model.League,
        offer.league_id,
    )
    league_name = (
        league_row.name if league_row else offer.league_id
    )

    rosters_by_league = await get_all_rosters_by_league(
        db=db,
        league_ids=[offer.league_id],
    )
    rosters = rosters_by_league.get(offer.league_id, [])
    counterparty = next(
        (
            roster
            for roster in rosters
            if roster.roster_id == offer.counterparty_roster_id
        ),
        None,
    )

    manager_user_id = counterparty.owner_id if counterparty else None

    if not manager_user_id:
        logger.warning(
            "Trade DM requested but counterparty roster %s in league %s "
            "has no owner — skipping.",
            offer.counterparty_roster_id,
            offer.league_id,
        )
        return

    # Build users_in_league_map for the trade card
    all_owner_ids = {r.owner_id for r in rosters if r.owner_id}
    users_result = await db.execute(
        select(model.User).where(model.User.user_id.in_(all_owner_ids))
    )
    user_map = {u.user_id: u for u in users_result.scalars()}

    users_in_league_map = {}
    for uid, u in user_map.items():
        users_in_league_map[uid] = {
            "user_id": u.user_id,
            "display_name": u.display_name,
            "avatar": u.avatar,
            "is_bot": False,
            "is_owner": (uid == sender_user_id),
            "league_id": offer.league_id,
            "metadata": {},
            "settings": None,
        }

    # Build added_picks for each side
    your_added_picks = [
        {
            "roster_id": str(p.og_roster_id or offer.your_roster_id),
            "season": str(p.season),
            "round": str(p.round),
            "owner_id": str(sender_user_id or ""),
            "previous_owner_id": str(manager_user_id or ""),
            "original_owner_id": str(p.og_roster_id or offer.counterparty_roster_id),
        }
        for p in (offer.receive_picks or [])
    ]

    counterparty_added_picks = [
        {
            "roster_id": str(p.og_roster_id or offer.counterparty_roster_id),
            "season": str(p.season),
            "round": str(p.round),
            "owner_id": str(manager_user_id or ""),
            "previous_owner_id": str(sender_user_id or ""),
            "original_owner_id": str(p.og_roster_id or offer.your_roster_id),
        }
        for p in (offer.send_picks or [])
    ]

    transactions_by_roster = {
        str(offer.your_roster_id): {
            "adds": offer.receive_player_ids or [],
            "drops": offer.send_player_ids or [],
            "added_picks": your_added_picks,
            "dropped_picks": [],
            "added_budget": [],
            "dropped_budget": [],
            "status": "proposed",
            "user": users_in_league_map.get(sender_user_id or "", {
                "user_id": sender_user_id or "",
                "display_name": sender_display_name,
                "avatar": None,
                "is_bot": False,
                "is_owner": True,
                "league_id": offer.league_id,
                "metadata": {},
                "settings": None,
            }),
        },
        str(offer.counterparty_roster_id): {
            "adds": offer.send_player_ids or [],
            "drops": offer.receive_player_ids or [],
            "added_picks": counterparty_added_picks,
            "dropped_picks": [],
            "added_budget": [],
            "dropped_budget": [],
            "status": "proposed",
            "user": users_in_league_map.get(manager_user_id, {
                "user_id": manager_user_id,
                "display_name": user_map[manager_user_id].display_name if manager_user_id in user_map else f"Roster {offer.counterparty_roster_id}",
                "avatar": None,
                "is_bot": False,
                "is_owner": False,
                "league_id": offer.league_id,
                "metadata": {},
                "settings": None,
            }),
        },
    }

    try:
        await send_trade_dm_to_manager(
            sleeper,
            transaction_id=transaction_id,
            league_id=offer.league_id,
            league_name=league_name,
            sender_display_name=sender_display_name,
            manager_user_id=manager_user_id,
            transactions_by_roster=transactions_by_roster,
            users_in_league_map=users_in_league_map,
        )
    except Exception:
        logger.exception(
            "Failed to send trade DM for league=%s transaction=%s "
            "— trade was already accepted.",
            offer.league_id,
            transaction_id,
        )
