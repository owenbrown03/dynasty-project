import time
import logging
from fastapi import HTTPException, status
from app.core.context import Context
from app.schemas.commissioner import (
    CommissionerPollBroadcastRequest,
    CommissionerPollBroadcastResponse,
    CommissionerPollBroadcastResult,
)
from app.services.leagues.selection import get_visible_owned_league_rows_by_sleeper_user_id

logger = logging.getLogger(__name__)


def _require_commissioner_workspace_context(ctx: Context) -> None:
    if ctx.site_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    if ctx.connection is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Linked Sleeper account required",
        )


async def broadcast_commissioner_poll(
    body: CommissionerPollBroadcastRequest,
    ctx: Context,
) -> CommissionerPollBroadcastResponse:
    _require_commissioner_workspace_context(ctx)

    if not ctx.sleeper_write or not ctx.sleeper_write.auth.is_authenticated():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sleeper write access required",
        )

    owned_rows = await get_visible_owned_league_rows_by_sleeper_user_id(
        db=ctx.db,
        sleeper_user_id=ctx.connection.sleeper_user_id or "",
        site_user_id=ctx.site_user.id,
        include_hidden=False,
    )

    owned_league_dict = {row.league.league_id: row.league for row in owned_rows}

    results = []
    success_count = 0

    closes_at_ms = None
    if body.expiration_days:
        # expiration in milliseconds
        closes_at_ms = int(time.time() * 1000) + body.expiration_days * 24 * 60 * 60 * 1000

    for league_id in body.league_ids:
        league = owned_league_dict.get(league_id)
        if not league:
            results.append(
                CommissionerPollBroadcastResult(
                    league_id=league_id,
                    success=False,
                    error="Not an owned league or league not found.",
                )
            )
            continue

        try:
            # 1. Create poll
            poll_id = await ctx.sleeper_write.create_poll(
                prompt=body.prompt,
                choices=body.choices,
                is_private=body.is_private,
                poll_type=body.poll_type,
            )

            # 2. Set expiration
            if closes_at_ms:
                await ctx.sleeper_write.set_poll_expiration(
                    poll_id=poll_id,
                    closes_at_timestamp_ms=closes_at_ms,
                )

            # 3. Send message
            await ctx.sleeper_write.send_poll_message(
                league_id=league_id,
                poll_id=poll_id,
                text=body.follow_up_message or "",
            )

            success_count += 1
            results.append(
                CommissionerPollBroadcastResult(
                    league_id=league_id,
                    league_name=league.name,
                    poll_id=poll_id,
                    success=True,
                )
            )
        except Exception as e:
            logger.exception(f"Failed to broadcast poll to league {league_id}")
            results.append(
                CommissionerPollBroadcastResult(
                    league_id=league_id,
                    league_name=league.name,
                    success=False,
                    error=str(e),
                )
            )

    return CommissionerPollBroadcastResponse(
        total_leagues=len(body.league_ids),
        successful_leagues=success_count,
        results=results,
    )
