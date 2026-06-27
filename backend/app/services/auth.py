from fastapi import HTTPException, APIRouter, status
from passlib.context import CryptContext

from app.schemas.auth import Login
from app.core.context import Context
from app.crud.auth.user import get_user_by_credentials, insert_user
from app.crud.auth.session import create_session_by_userid, insert_session_by_userid, delete_session

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

async def register(credentials: Login, ctx: Context):
    db_user = await get_user_by_credentials(credentials, ctx.db)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Username already taken"
        )
    return await insert_user(credentials, ctx.db)

async def login(credentials: Login, ctx: Context):
    db_user = await get_user_by_credentials(credentials, ctx.db)
    if not db_user or not pwd_context.verify(credentials.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect username or password"
        )
    return await insert_session_by_userid(db_user.id, ctx.session, ctx.db)

async def logout(ctx: Context):
    if not ctx.session or not ctx.session.site_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    await delete_session(ctx.session, ctx.response, ctx.db)
    return ctx.session.site_user_id

async def validate(ctx: Context):
    try:
        if ctx.session and ctx.session.site_user_id:
            await create_session_by_userid(ctx.session.site_user_id, ctx.response, ctx.db)
            return {"authenticated": True, "user_id": ctx.session.site_user_id}
        ctx.response.delete_cookie("session_id")
        return {"authenticated": False, "user_id": None}
    except Exception as e:
        print(f"Validation error: {e}")
        return {"authenticated": False, "user_id": None}
    

async def me(ctx: Context):
    if not ctx.site_user:
        return {"authenticated": False}

    return {"authenticated": True}