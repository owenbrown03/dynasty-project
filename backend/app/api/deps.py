from fastapi import HTTPException, status, Cookie, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.integrations.sleeper.client import SleeperClient
from app.models.auth import UserSession, SiteUser
from app.models.sleeper.connection import SleeperConnection
from app.core.security import decrypt_token
from app.crud.auth.user import get_user_by_session
from app.crud.auth.session import get_session_by_token
from app.crud.sleeper.connection import get_connection_by_session, get_connection_by_user


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_session(
    db: AsyncSession = Depends(get_db),
    session_token: str | None = Cookie(None),
) -> UserSession | None:

    if not session_token:
        return None

    return await get_session_by_token(
        session_token,
        db,
    )


async def get_current_user(
    session: UserSession | None = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> SiteUser:

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    user = await get_user_by_session(
        session,
        db,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        )

    return user


async def get_optional_user(
    session: UserSession | None = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> SiteUser | None:

    if not session:
        return None

    return await get_user_by_session(
        session,
        db,
    )


async def get_sleeper_connection(
    session: UserSession | None = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> SleeperConnection | None:

    if not session:
        return None

    connection = await get_connection_by_session(
        session,
        db,
    )

    if connection:
        return connection

    user = await get_user_by_session(
        session,
        db,
    )

    if not user:
        return None

    return await get_connection_by_user(
        user,
        db,
    )


async def get_user_sleeper_client(
    connection: SleeperConnection | None = Depends(
        get_sleeper_connection
    ),
) -> SleeperClient:

    token = None

    if connection and connection.encrypted_token:
        token = decrypt_token(
            connection.encrypted_token
        )

    return SleeperClient(
        token=token,
    )


async def require_sleeper_token(
    sleeper: SleeperClient = Depends(
        get_user_sleeper_client
    ),
) -> SleeperClient:

    if not sleeper.token:
        raise HTTPException(
            status_code=400,
            detail="Sleeper account not connected",
        )

    return sleeper