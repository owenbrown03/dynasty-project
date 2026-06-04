from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import UserSession
from app.integrations.sleeper.client import SleeperClient
from app.crud.sleeper.connection import get_connection_by_session

async def get(
    sleeper: SleeperClient,
    session: UserSession,
    db: AsyncSession,
):
    if not session:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    connection = await get_connection_by_session(session, db)

    return {
        "sleeper_user_id": connection.sleeper_user_id,
        "username": await sleeper.read.get_user_details_by_user_id(connection.sleeper_user_id).display_name,
        "can_read": connection.sleeper_user_id is not None,
        "can_write": connection.encrypted_token is not None,
    }