from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
 
from app.models.auth import SiteUser, UserSession
from app.integrations.sleeper.client import SleeperClient
from app.models.sleeper.connection import SleeperConnection
from app.core.security import encrypt_token
from app.crud.sleeper.user import get_userid_by_username

async def upsert_sleeper_connection(
    *,
    db: AsyncSession,
    sleeper: SleeperClient,
    site_user: SiteUser,
    session: UserSession,
    sleeper_username: str | None = None,
    token: str | None = None,
):

    if sleeper_username:
        sleeper_user_id = await get_userid_by_username(db, sleeper_username, sleeper)
    if token:
        encrypted_token = encrypt_token(token)

    stmt = select(SleeperConnection).where(
        (SleeperConnection.site_user_id == site_user.id)
        if site_user else
        (SleeperConnection.session_id == session.id)
    )

    result = await db.execute(stmt)
    conn = result.scalar_one_or_none()

    # -----------------------------
    # CASE 1: create new connection
    # -----------------------------
    if not conn:
        conn = SleeperConnection(
            site_user_id=site_user.id if site_user else None,
            session_id=session.id if session else None,
            sleeper_user_id=sleeper_user_id if sleeper_user_id else "",
            encrypted_token=encrypted_token if encrypted_token else "",
            source="session" if session and not site_user else "user",
            linked_at=datetime.now(),
        )
        db.add(conn)
        await db.commit()
        return conn

    # -----------------------------
    # CASE 2: enrich existing record
    # -----------------------------
    if sleeper_user_id and not conn.sleeper_user_id:
        conn.sleeper_user_id = sleeper_user_id

    if encrypted_token and not conn.encrypted_token:
        conn.encrypted_token = encrypted_token

    if site_user:
        conn.site_user_id = site_user.id
        conn.session_id = None
        conn.source = "user"

    conn.linked_at = datetime.now()

    await db.commit()
    return conn

async def get_connection_by_user(
    site_user: SiteUser, 
    db: AsyncSession,
) -> SleeperConnection | None:
    
    stmt = select(SleeperConnection).where(
        SleeperConnection.site_user_id == site_user.id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_connection_by_session(
    session: UserSession, 
    db: AsyncSession,
) -> SleeperConnection | None:
    
    stmt = select(SleeperConnection).where(
        SleeperConnection.session_id == session.id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()