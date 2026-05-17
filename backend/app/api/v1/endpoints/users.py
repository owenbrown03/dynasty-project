from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_session
from app.crud.user import sync_user_data
from app.crud.roster import get_user_rosters
from app.services import sleeper

router = APIRouter()

@router.post("/{username}/sync")
async def sync_user_data_endpoint(username: str, db: Session = Depends(get_session)):
    username_details = await sleeper.get_username_details(username)
    if not username_details:
        raise HTTPException(status_code=404, detail="User not found")

    await sync_user_data(db, username_details['user_id'], "2026") #TODO: season should be dynamic
    return {"status": "success"}

@router.get("/{username}/rosters")
async def get_user_rosters_endpoint(username: str, db: Session = Depends(get_session)):
    username_details = await sleeper.get_username_details(username)
    return await get_user_rosters(db, username_details['user_id'])