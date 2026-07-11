import logging

from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.schemas.auth import Login, ThemePreferenceUpdate
from app.core.context import Context
from app.crud.auth.user import (
    get_theme_preference,
    get_user_by_credentials,
    insert_user,
    reconcile_session_theme_preference,
    set_theme_preference,
)
from app.crud.auth.session import (
    create_session_by_userid,
    get_session_theme_preference,
    insert_session_by_userid,
    delete_session,
    set_session_theme_preference,
)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
logger = logging.getLogger(__name__)

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
    session = await insert_session_by_userid(
        db_user.id,
        ctx.session,
        ctx.db,
    )

    await reconcile_session_theme_preference(
        user=db_user,
        session=session,
        db=ctx.db,
    )

    return session

async def logout(ctx: Context):
    if not ctx.session or not ctx.session.site_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    theme_preference = (
        get_session_theme_preference(
            ctx.session,
        )
        or get_theme_preference(
            ctx.site_user,
        )
    )

    await delete_session(ctx.session, ctx.response, ctx.db)

    new_session = await create_session_by_userid(
        None,
        ctx.response,
        ctx.db,
    )

    if theme_preference is not None:
        await set_session_theme_preference(
            session=new_session,
            theme_preference=theme_preference,
            db=ctx.db,
        )

    return ctx.session.site_user_id

async def validate(ctx: Context):
    try:
        if ctx.session and ctx.session.site_user_id:
            await create_session_by_userid(ctx.session.site_user_id, ctx.response, ctx.db)
            return {"authenticated": True, "user_id": ctx.session.site_user_id}
        ctx.response.delete_cookie("session_id")
        return {"authenticated": False, "user_id": None}
    except Exception as e:
        logger.exception("Session validation failed")
        return {"authenticated": False, "user_id": None}
    

async def me(ctx: Context):
    if not ctx.site_user:
        return {"authenticated": False}

    return {"authenticated": True}


async def update_theme(
    body: ThemePreferenceUpdate,
    ctx: Context,
):
    session = await set_session_theme_preference(
        session=ctx.session,
        theme_preference=body.theme_preference,
        db=ctx.db,
    )

    if ctx.site_user:
        user = await set_theme_preference(
            user=ctx.site_user,
            theme_preference=body.theme_preference,
            db=ctx.db,
        )
        return {
            "theme_preference": (
                user.settings.get("theme_preference")
            ),
        }

    return {
        "theme_preference": (
            session.settings.get("theme_preference")
        ),
    }
