from fastapi import HTTPException, APIRouter, Response, status
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.schemas.auth import Login
from app.models.auth import UserSession
from app.crud.auth.user import get_user_by_credentials, insert_user
from app.crud.auth.session import insert_session_by_userid, delete_session

router = APIRouter()

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

async def register(credentials: Login, db: AsyncSession):
    db_user = await get_user_by_credentials(credentials, db)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Username already taken"
        )
    return await insert_user(credentials, db)

async def login(credentials: Login, response: Response, db: AsyncSession):
    db_user = await get_user_by_credentials(credentials, db)
    if not db_user or not pwd_context.verify(credentials.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect username or password"
        )
    return await insert_session_by_userid(db_user.id, response, db)

async def logout(response: Response, session: UserSession, db: AsyncSession):
    if not session or not session.site_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    await delete_session(session, response, db)
    return session.site_user_id

async def validate(response: Response, session: UserSession, db: AsyncSession):
    try:
        if session and session.site_user_id:
            await insert_session_by_userid(session.site_user_id, response, db)
            return {"authenticated": True, "user_id": session.site_user_id}
        response.delete_cookie("session_id")
        return {"authenticated": False, "user_id": None}
    except Exception as e:
        print(f"Validation error: {e}")
        return {"authenticated": False, "user_id": None}