from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import UserSession, SiteUser
from app.integrations.sleeper.client import SleeperClientManager
from app.crud.sleeper.connection import upsert_sleeper_connection
from app.api.deps import get_db, get_current_session, get_current_user, get_user_sleeper_client
from app.services.sleeper.connection import get

router = APIRouter()

@router.get('')
async def get_endpoint(
    session: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    sleeper = SleeperClientManager.get()
    return await get(sleeper, session, db)

@router.post('/upsert/{sleeper_username}/')
async def upsert_endpoint(
    sleeper_username: str,
    user: SiteUser = Depends(get_current_session),
    session: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sleeper = SleeperClientManager.get()
    return await upsert_sleeper_connection(
        db=db,
        sleeper=sleeper,
        user=user,
        session=session,
        sleeper_username=sleeper_username,
    )