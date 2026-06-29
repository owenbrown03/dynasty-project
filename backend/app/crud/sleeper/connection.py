import logging
from datetime import datetime
from sqlmodel import select
 
from app.core.context import Context
from app.models.db.sleeper.connection import SleeperConnection

logger = logging.getLogger(__name__)


async def upsert_connection(
    ctx: Context,
    *,
    sleeper_username: str | None = None,
    sleeper_user_id: str | None = None,
    encrypted_token: str | None = None,
):
    owner_filter = (
        SleeperConnection.site_user_id == ctx.site_user.id
        if ctx.site_user
        else SleeperConnection.session_id == ctx.session.id
    )

    conn = (
        await ctx.db.execute(
            select(SleeperConnection).where(owner_filter)
        )
    ).scalars().first()

    if not conn:
        conn = SleeperConnection(
            site_user_id=ctx.site_user.id if ctx.site_user else None,
            session_id=ctx.session.id if ctx.session else None,
            sleeper_username=sleeper_username,
            sleeper_user_id=sleeper_user_id,
            encrypted_token=encrypted_token,
        )
        ctx.db.add(conn)

    else:
        if sleeper_username is not None:
            conn.sleeper_username = sleeper_username
        
        if sleeper_user_id is not None:
            conn.sleeper_user_id = sleeper_user_id

        if encrypted_token is not None:
            conn.encrypted_token = encrypted_token

        conn.linked_at = datetime.now()

        if ctx.site_user and conn.session_id:
            conn.site_user_id = ctx.site_user.id
            conn.session_id = None

    await ctx.db.commit()
    await ctx.db.refresh(conn)
    return conn

async def reconcile(ctx: Context):
    if not ctx.site_user or not ctx.session:
        return None

    session_conn = (
        await ctx.db.execute(
            select(SleeperConnection).where(
                SleeperConnection.session_id == ctx.session.id
            )
        )
    ).scalars().first()

    user_conn = (
        await ctx.db.execute(
            select(SleeperConnection).where(
                SleeperConnection.site_user_id == ctx.site_user.id
            )
        )
    ).scalars().first()

    if not session_conn:
        logger.info("No session connection, returning")
        return user_conn

    if not user_conn:
        logger.info("No user connection, returning")
        session_conn.site_user_id = ctx.site_user.id
        session_conn.session_id = None
        await ctx.db.commit()
        return session_conn

    # merge session → user
    if session_conn.sleeper_user_id:
        user_conn.sleeper_user_id = session_conn.sleeper_user_id

    if session_conn.encrypted_token:
        user_conn.encrypted_token = session_conn.encrypted_token

    await ctx.db.delete(session_conn)
    await ctx.db.commit()
    logger.info("Merged, returning")
    return user_conn