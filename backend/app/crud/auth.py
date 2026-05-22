import secrets, os
from fastapi import Response, Request

from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.auth import SiteUser, UserSession
from app.schemas.auth import Login

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

async def get_user(credentials: Login, db: AsyncSession):
    stmt = select(SiteUser).where(SiteUser.email == credentials.email)
    results = await db.execute(stmt)
    db_user = results.scalar_one_or_none()
    return db_user
    
async def insert_user(credentials: Login, db: AsyncSession):
    hashed_pw = pwd_context.hash(credentials.password)
    new_user = SiteUser(
        email=credentials.email,
        hashed_password=hashed_pw
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return {"message": "User inserted"}

async def insert_session(user_id: str, response: Response, db: AsyncSession):
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
    return {"message": "Session inserted"}

async def get_session(request: Request, db: AsyncSession):
    token = request.cookies.get("session_token")
    if not token:
        return None
    try:
        stmt = select(UserSession).where(UserSession.session_token == token)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    except Exception as e:
        print(f"Database error during session lookup: {e}")
        return None
        
async def delete_session(session: UserSession, response: Response, db: AsyncSession):
    stmt = select(UserSession).where(UserSession.session_token == session.session_token)
    result = await db.execute(stmt)
    db_session = result.scalar_one_or_none()
    if db_session:
        await db.delete(db_session)
        await db.commit()    
    response.delete_cookie(
        key="session_token",
        httponly=True,
        secure=os.getenv("ENVIRONMENT") == "production",
        samesite="lax"
    )
    return {"message": "Session deleted"}

async def insert_sleeper_id(sleeper_id: str, site_user_id: str, db: AsyncSession):
    result = await db.execute(select(SiteUser).where(SiteUser.id == site_user_id))
    user = result.scalar_one_or_none()
    if user:
        user.sleeper_id = sleeper_id
        await db.commit()
        await db.refresh(user)
        return {"message": "Sleeper id inserted"}
    else:
        return {"message": "User not in database"}
    
async def get_sleeper_id(site_user_id: str, db: AsyncSession):
    result = await db.execute(select(SiteUser).where(SiteUser.id == site_user_id))
    return result.scalar_one_or_none().sleeper_id
