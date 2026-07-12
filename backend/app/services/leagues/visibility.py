from __future__ import annotations

from fastapi import HTTPException, status

from app.core.context import Context
from app.crud.sleeper.personal import (
    hide_league,
    unhide_league,
)
from app.schemas.league import LeagueVisibilityItem


def _require_site_user(
    ctx: Context,
) -> None:
    if ctx.site_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )


async def set_league_visibility(
    *,
    ctx: Context,
    league_id: str,
    hidden: bool,
) -> LeagueVisibilityItem:
    _require_site_user(
        ctx,
    )

    if hidden:
        await hide_league(
            db=ctx.db,
            site_user_id=ctx.site_user.id,
            league_id=league_id,
        )
    else:
        await unhide_league(
            db=ctx.db,
            site_user_id=ctx.site_user.id,
            league_id=league_id,
        )

    return LeagueVisibilityItem(
        league_id=league_id,
        hidden=hidden,
    )
