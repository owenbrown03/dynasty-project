from __future__ import annotations

from fastapi import HTTPException, status

from app.core.context import Context
from app.crud.sleeper.personal import upsert_user_note
from app.schemas.league import UserLeagueNoteResponse


def _require_site_user(
    ctx: Context,
) -> None:
    if ctx.site_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )


async def save_user_note(
    *,
    ctx: Context,
    league_id: str,
    note: str,
) -> UserLeagueNoteResponse:
    _require_site_user(
        ctx,
    )

    note_record = await upsert_user_note(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
        league_id=league_id,
        note=note,
    )

    return UserLeagueNoteResponse(
        league_id=note_record.league_id,
        note=note_record.note,
    )
