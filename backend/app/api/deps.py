from fastapi import HTTPException, Request, Response, Cookie, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import AsyncSessionLocal
from app.models.db.auth import UserSession, SiteUser
from app.models.db.sleeper.connection import SleeperConnection
from app.integrations.sleeper.client import SleeperClient
from app.infrastructure.redis.client import RedisClient
from app.core.context import Context
from app.core.security import decrypt_token
from app.crud.auth.user import get_user_by_session
from app.crud.auth.session import get_session_by_token, create_session_by_userid
from app.integrations.sleeper.factory import get_sleeper_client

async def get_db():
    async with AsyncSessionLocal() as db:
        yield db


async def get_current_session(
    response: Response,
    db: AsyncSession = Depends(get_db),
    session_token: str | None = Cookie(None),
) -> UserSession:
    
    if session_token:
        session = await get_session_by_token(session_token, db)
        if session:
            return session

    new_session = await create_session_by_userid(None, response, db)
    await db.refresh(new_session)
    return new_session


async def get_current_user(
    session: UserSession | None = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> SiteUser:

    if not session:
        raise HTTPException(401, "Authentication required")

    user = await get_user_by_session(session, db)

    if not user:
        raise HTTPException(401, "Invalid session")

    return user


async def get_optional_user(
    session: UserSession | None = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> SiteUser | None:

    if not session:
        return None

    return await get_user_by_session(session, db)


async def get_sleeper_connection(
    db: AsyncSession = Depends(get_db),
    session: UserSession = Depends(get_current_session),
    user: SiteUser | None = Depends(get_optional_user),
) -> SleeperConnection | None:

    if user:
        stmt = select(SleeperConnection).where(
            SleeperConnection.site_user_id == user.id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    stmt = select(SleeperConnection).where(
        SleeperConnection.session_id == session.id
    )
    result = await db.execute(stmt)

    return result.scalar_one_or_none()


async def get_user_sleeper_client(
    connection: SleeperConnection | None = Depends(
        get_sleeper_connection,
    ),
) -> SleeperClient:

    sleeper = await get_sleeper_client()

    if not connection or not connection.encrypted_token:
        return sleeper

    token = decrypt_token(
        connection.encrypted_token,
    )

    return sleeper.with_token(token)


async def get_redis_client(
    request: Request,
) -> RedisClient:
    return RedisClient(request.app.state.redis)


async def get_context(
    response: Response,
    db: AsyncSession = Depends(get_db),
    session: UserSession = Depends(get_current_session),
    site_user: SiteUser | None = Depends(get_optional_user),
    connection: SleeperConnection | None = Depends(get_sleeper_connection),
    sleeper: SleeperClient | None = Depends(get_user_sleeper_client),
    redis: RedisClient | None = Depends(get_redis_client),
) -> Context:

    return Context(
        response=response,
        db=db,
        session=session,
        site_user=site_user,
        connection=connection,
        sleeper=sleeper,
        redis=redis,
    )