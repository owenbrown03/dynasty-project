import secrets, os, uuid
from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.auth import UserSession

async def insert_session_by_userid(
    user_id: uuid.UUID, 
    response: Response, 
    db: AsyncSession
):

    token = secrets.token_hex(32)
    new_session = UserSession(session_token=token, site_user_id=user_id)
    db.add(new_session)
    await db.commit()
    response.set_cookie(
        key="session_token", 
        value=token, 
        httponly=True, 
        secure=os.getenv("ENVIRONMENT") == "production",
        samesite="lax"
    )
    return new_session

async def delete_session(
    session: UserSession,
    response: Response,
    db: AsyncSession,
):
    await db.delete(session)
    await db.commit()
    response.delete_cookie(
        key="session_token",
        httponly=True,
        secure=os.getenv("ENVIRONMENT") == "production",
        samesite="lax",
    )

async def get_session_by_token(
    token: str, 
    db: AsyncSession
) -> UserSession | None:
    
    stmt = select(UserSession).where(
        UserSession.session_token == token
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()