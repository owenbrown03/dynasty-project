from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.db.auth import SiteUser, UserSession
from app.schemas.auth import Login
from app.crud.auth.session import get_session_by_token

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

async def insert_user(
    credentials: Login,
    db: AsyncSession
):
    
    hashed_pw = pwd_context.hash(credentials.password)
    new_user = SiteUser(
        email=credentials.email,
        hashed_password=hashed_pw
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def get_user_by_credentials(
    credentials: Login, 
    db: AsyncSession
) -> SiteUser:
    
    stmt = select(SiteUser).where(SiteUser.email == credentials.email)
    results = await db.execute(stmt)
    db_user = results.scalar_one_or_none()
    return db_user
    
async def get_user_by_token(
    token: str,
    db: AsyncSession,
) -> SiteUser | None:

    session = await get_session_by_token(
        token,
        db,
    )

    if not session:
        return None

    return await get_user_by_session(
        session,
        db,
    )

async def get_user_by_session(
    session: UserSession | None,
    db: AsyncSession,
) -> SiteUser | None:
    
    if not session or not session.site_user_id:
        return None

    return await db.get(
        SiteUser,
        session.site_user_id,
    )