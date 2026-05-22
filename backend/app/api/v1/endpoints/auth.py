from fastapi import APIRouter, Response, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import Login
from app.api.deps import get_session
from app.services.auth import register, login, logout, validate, sync_sleeper, get_sleeper

router = APIRouter()

@router.post("/register")
async def register_endpoint(credentials: Login, response: Response, db: AsyncSession = Depends(get_session)):
    await register(credentials, db)
    await login(credentials, response, db)
    return {
        "status": "queued", 
        "message": "Registering...",
        "username": credentials.email
    } 

@router.post("/login")
async def login_endpoint(credentials: Login, response: Response, db: AsyncSession = Depends(get_session)):
    await login(credentials, response, db)
    return {
        "status": "queued", 
        "message": "Logging in...",
        "username": credentials.email
    } 

@router.post("/logout")
async def logout_endpoint(request: Request, response: Response, db: AsyncSession = Depends(get_session)):
    site_user_id = await logout(request, response, db)
    return {
        "status": "queued", 
        "message": "Logging out...",
        "username": site_user_id
    } 

@router.get("/validate")
async def validate_endpoint(request: Request, response: Response, db: AsyncSession = Depends(get_session)):
    result = await validate(request, response, db)
    return {
        "status": "success", 
        "data": result
    }

@router.post("/{sleeper_username}/sync-sleeper")
async def sync_sleeper_endpoint(sleeper_username: str, request: Request, db: AsyncSession = Depends(get_session)):
    await sync_sleeper(sleeper_username, request, db)
    return {
        "status": "queued", 
        "message": "Syncing sleeper...",
        "username": sleeper_username
    } 

@router.get("/sleeper")
async def get_sleeper_endpoint(request: Request, db: AsyncSession = Depends(get_session)):
    sleeper_data = await get_sleeper(request, db)
    return {
        "status": "success",
        "message": "Getting sleeper username",
        "data": sleeper_data
    }