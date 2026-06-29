import secrets, os, uuid
from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, delete

from app.models.db.auth import UserSession

async def create_session_by_userid(
    user_id: uuid.UUID, 
    response: Response, 
    db: AsyncSession
):

    token = secrets.token_hex(32)
    new_session = UserSession(session_token=token, site_user_id=user_id)
    db.add(new_session)
    await db.commit()
    is_prod = os.getenv("ENVIRONMENT") == "production"
    response.set_cookie(
        key="session_token", 
        value=token, 
        httponly=True, 
        secure=is_prod,
        samesite="lax",
        domain=None,
    )
    return new_session

async def insert_session_by_userid(
    site_user_id: uuid.UUID, 
    session: UserSession, 
    db: AsyncSession
):
    session.site_user_id = site_user_id
    await db.commit()
    await db.refresh(session)
    return session

async def delete_session(
    session: UserSession,
    response: Response,
    db: AsyncSession,
):
    await db.execute(
        delete(UserSession).where(UserSession.id == session.id)
    )

    await db.commit()

    is_prod = os.getenv("ENVIRONMENT") == "production"
    response.delete_cookie(
        key="session_token",
        httponly=True,
        secure=is_prod,
        samesite="lax",
        domain=None,
    )

    return {"status": "logged_out"}

async def get_session_by_token(
    token: str, 
    db: AsyncSession
) -> UserSession | None:
    
    stmt = select(UserSession).where(
        UserSession.session_token == token
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()