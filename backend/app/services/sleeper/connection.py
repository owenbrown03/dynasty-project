from app.core.context import Context
from app.core.security import encrypt_token
from app.crud.sleeper.connection import upsert_connection
from app.crud.sleeper.user import get_userid_by_username


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
        sleeper_username=sleeper_username,
        sleeper_user_id=sleeper_user_id,
        encrypted_token=encrypted_token,
    )