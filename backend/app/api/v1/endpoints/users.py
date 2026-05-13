from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.crud.user import create_user_data
from app.crud.roster import get_user_rosters
from app.services import sleeper

router = APIRouter()

@router.post("/{username}/sync")
async def sync_user_data(username: str, db: Session = Depends(get_db)):
    user_data = await sleeper.get_username_details(username)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    await create_user_data(db, user_data['user_id'], "2026") #TODO: season should be dynamic
    return {"status": "success"}

@router.get("/{username}/rosters")
async def get_rosters(username: str, db: Session = Depends(get_db)):
    user_data = await sleeper.get_username_details(username)
    return await get_user_rosters(db, user_data['user_id'])