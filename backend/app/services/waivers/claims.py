from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.sleeper.client import SleeperClient
from app.models.db.sleeper.api import League, Roster
from app.models.db.sleeper.connection import SleeperConnection
from app.schemas.waivers import (
    WaiverClaimRequest,
    WaiverClaimResponse,
)
from app.services.waivers.payloads import build_waiver_claim_variables


def find_transaction_id(
    payload: object,
) -> str | None:
    """
    Sleeper mutation response shapes can vary by operation.

    Find transaction_id recursively rather than coupling this endpoint
    to one exact GraphQL response nesting structure.
    """

    if isinstance(payload, dict):
        transaction_id = payload.get("transaction_id")

        if transaction_id:
            return str(transaction_id)

        for value in payload.values():
            found = find_transaction_id(value)

            if found is not None:
                return found

    if isinstance(payload, list):
        for value in payload:
            found = find_transaction_id(value)

            if found is not None:
                return found

    return None


async def get_owned_roster_for_claim(
    *,
    db: AsyncSession,
    connection: SleeperConnection,
    league_id: str,
    roster_id: int,
) -> tuple[Roster, League]:
    """
    Returns the requested roster only when it belongs to the currently
    connected Sleeper account.
    """

    if not connection.sleeper_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Connected Sleeper account is missing a Sleeper user ID."
            ),
        )

    result = await db.execute(
        select(Roster, League)
        .join(
            League,
            League.league_id == Roster.league_id,
        )
        .where(
            Roster.league_id == league_id,
            Roster.roster_id == roster_id,
            Roster.owner_id == connection.sleeper_user_id,
        )
    )

    row = result.one_or_none()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not own this roster or it is unavailable "
                "for the connected Sleeper account."
            ),
        )

    return row


def get_claim_block_reason(
    *,
    roster: Roster,
    league: League,
) -> str | None:
    roster_spots_available = roster.open_roster_spots(
        league,
    )

    if roster_spots_available < 0:
        return (
            "This roster is "
            f"{abs(roster_spots_available)} player"
            f"{'s' if abs(roster_spots_available) != 1 else ''} "
            "over its allowed roster capacity. "
            "Remove players first before submitting a waiver claim."
        )

    return None


def validate_claim(
    *,
    claim: WaiverClaimRequest,
    roster: Roster,
    league: League,
) -> None:
    """
    Validates a waiver claim before sending the Sleeper write mutation.

    Rules:
    - Positive open spots: a drop is optional.
    - Zero open spots: exactly one drop is required.
    - Negative open spots: block all waiver claims because add/drop
      leaves the roster over capacity.
    """

    claim_block_reason = get_claim_block_reason(
        roster=roster,
        league=league,
    )

    if claim_block_reason is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=claim_block_reason,
        )

    roster_player_ids = set(
        roster.players or [],
    )

    has_open_roster_spot = (
        roster.open_roster_spots(league) > 0
    )

    if (
        claim.drop_player_id is None
        and not has_open_roster_spot
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "A drop player is required because this roster "
                "does not have an open roster spot."
            ),
        )

    if (
        claim.drop_player_id is not None
        and claim.add_player_id == claim.drop_player_id
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The add player and drop player must be different."
            ),
        )

    if (
        claim.drop_player_id is not None
        and claim.drop_player_id not in roster_player_ids
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The selected drop player is not currently "
                "on this roster."
            ),
        )

    if claim.add_player_id in roster_player_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The selected add player is already on this roster."
            ),
        )

    faab_remaining = roster.faab_remaining(
        league,
    )

    if claim.bid > faab_remaining:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Bid of ${claim.bid} exceeds your remaining "
                f"FAAB balance of ${faab_remaining}."
            ),
        )


async def submit_claim(
    *,
    db: AsyncSession,
    connection: SleeperConnection | None,
    sleeper: SleeperClient,
    claim: WaiverClaimRequest,
) -> WaiverClaimResponse:
    """
    Validates and submits one authenticated Sleeper waiver claim.
    """

    if connection is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Connect a Sleeper account before submitting a claim.",
        )

    if not connection.encrypted_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Enable Sleeper write access before submitting "
                "a waiver claim."
            ),
        )

    roster, league = await get_owned_roster_for_claim(
        db=db,
        connection=connection,
        league_id=claim.league_id,
        roster_id=claim.roster_id,
    )

    validate_claim(
        claim=claim,
        roster=roster,
        league=league,
    )

    sleeper_variables = build_waiver_claim_variables(
        claim,
    )

    result: dict[str, Any] = (
        await sleeper.write.submit_waiver_claim(
            league_id=claim.league_id,
            **sleeper_variables,
        )
    )

    transaction_id = find_transaction_id(
        result,
    )

    if transaction_id is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Sleeper did not return a transaction ID for "
                "the submitted waiver claim."
            ),
        )

    return WaiverClaimResponse(
        transaction_id=transaction_id,
    )