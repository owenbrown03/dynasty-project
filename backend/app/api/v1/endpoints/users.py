from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import sleeper
from app.api.deps import get_session
from app.crud.user import sync_user_data
from app.crud.roster import get_user_rosters, get_user_orphans

router = APIRouter()

@router.post("/{username}/sync")
async def sync_user_data_endpoint(username: str, db: AsyncSession = Depends(get_session)):
    clean_username = username.strip()
    username_details = await sleeper.get_username_details(clean_username)
    if not username_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{clean_username}' could not be located in core schemas."
        )
    await sync_user_data(db, username_details['user_id'])
    return {"status": "success"}

@router.get("/{username}/rosters")
async def get_user_rosters_endpoint(username: str, db: AsyncSession = Depends(get_session)):
    username_details = await sleeper.get_username_details(username)
    return await get_user_rosters(db, username_details['user_id'])

@router.get("/{username}/orphans")
async def get_user_orphans_endpoint(username: str, db: AsyncSession = Depends(get_session)):
    username_details = await sleeper.get_username_details(username)
    return await get_user_orphans(db, username_details['user_id'])