from fastapi import HTTPException, APIRouter, Response, Request, status
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import Login
from app.crud.auth import get_user, insert_user, insert_session, get_session, delete_session, insert_sleeper_id, get_sleeper_id
from app.crud.user import user_id_lookup, username_lookup

router = APIRouter()

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

async def register(credentials: Login, db: AsyncSession):
    db_user = await get_user(credentials, db)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Username already taken"
        )
    await insert_user(credentials, db)

async def login(credentials: Login, response: Response, db: AsyncSession):
    db_user = await get_user(credentials, db)
    if not db_user or not pwd_context.verify(credentials.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect username or password"
        )
    await insert_session(db_user.id, response, db)

async def logout(request: Request, response: Response, db: AsyncSession):
    session = await get_session(request, db)
    if not session or not session.site_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    await delete_session(session, response, db)
    return session.site_user_id

async def validate(request: Request, response: Response, db: AsyncSession):
    try:
        session = await get_session(request, db)
        if session and session.site_user_id:
            await insert_session(session.site_user_id, response, db)
            return {"authenticated": True, "user_id": session.site_user_id}
        response.delete_cookie("session_id")
        return {"authenticated": False, "user_id": None}
    except Exception as e:
        print(f"Validation error: {e}")
        return {"authenticated": False, "user_id": None}
    
async def sync_sleeper(sleeper_username: str, request: Request, db: AsyncSession):
    session = await get_session(request, db)
    if not session or not session.site_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    user_id = await user_id_lookup(db, sleeper_username)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sleeper user not found")
    await insert_sleeper_id(user_id, session.site_user_id, db)

async def get_sleeper(request: Request, db: AsyncSession):
    session = await get_session(request, db)
    if not session or not session.site_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    sleeper_id = await get_sleeper_id(session.site_user_id, db)
    if not sleeper_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sleeper ID not linked")
    username = await username_lookup(db, sleeper_id)  
    if not username:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sleeper user not found")
    return {"sleeper_username": username}