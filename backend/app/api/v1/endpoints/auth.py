from fastapi import APIRouter, Response, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import UserSession
from app.schemas.auth import Login
from app.api.deps import get_db, get_current_session
from app.services.auth import register, login, logout, validate

router = APIRouter()

@router.post("/register")
async def register_endpoint(
    credentials: Login,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    await register(credentials, db)
    await login(credentials, response, db)
    return {
        "status": "queued", 
        "message": "Registering...",
        "username": credentials.email
    } 

@router.post("/login")
async def login_endpoint(
    credentials: Login,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    await login(credentials, response, db)
    return {
        "status": "queued", 
        "message": "Logging in...",
        "username": credentials.email
    } 

@router.post("/logout")
async def logout_endpoint(
    response: Response,
    session: UserSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    site_user_id = await logout(response, session, db)
    return {
        "status": "queued", 
        "message": "Logging out...",
        "username": site_user_id
    } 

@router.get("/validate")
async def validate_endpoint(
    response: Response,
    session: UserSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    result = await validate(response, session, db)
    return {
        "status": "success", 
        "data": result
    }