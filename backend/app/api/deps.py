# app/api/deps.py
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.models.auth import SiteUser, UserSession
from app.core.database import AsyncSessionLocal

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(
    db: AsyncSession = Depends(get_session),
    session_token: Optional[str] = Cookie(None)
) -> Optional[SiteUser]:
    
    if not session_token:
        return None

    stmt = select(UserSession).where(UserSession.session_token == session_token)
    results = await db.execute(stmt)
    
    user_session = results.scalar_one_or_none()
    if not user_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    
    user = await db.get(SiteUser, user_session.site_user_id)    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    return user