from fastapi import HTTPException

from app.schemas.sleeper.connection import SleeperConnectionResponse
from app.core.context import Context
from app.core.security import encrypt_token
from app.crud.sleeper.connection import upsert_connection
from app.crud.sleeper.user import get_userid_by_username

async def get(ctx: Context) -> SleeperConnectionResponse:

    if not ctx.connection or not ctx.connection.sleeper_user_id:
        raise HTTPException(400, "Not linked")

    user = await ctx.sleeper.read.get_user_details_by_user_id(
        ctx.connection.sleeper_user_id
    )

    return SleeperConnectionResponse(
        sleeper_user_id=ctx.connection.sleeper_user_id,
        username=user.display_name,
        can_read=True,
        can_write=ctx.can_write
    )

async def upsert(
    ctx: Context,
    *,
    sleeper_username: str | None = None,
    token: str | None = None,
):
    sleeper_user_id = None
    encrypted_token = None

    if sleeper_username:
        sleeper_user_id = await get_userid_by_username(
            ctx.db, 
            ctx.sleeper,
            sleeper_username,
        )

    if token:
        encrypted_token = encrypt_token(token)

    return await upsert_connection(
        ctx,
        sleeper_user_id=sleeper_user_id,
        encrypted_token=encrypted_token,
    )