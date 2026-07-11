import logging

from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.schemas.auth import (
    AuthSessionResponse,
    Login,
    ThemePreferenceResponse,
    ThemePreferenceUpdate,
    ValuePreferenceResponse,
    ValuePreferenceUpdate,
)
from app.core.context import Context
from app.crud.auth.user import (
    get_theme_preference,
    get_value_preference,
    get_user_by_credentials,
    insert_user,
    reconcile_session_theme_preference,
    reconcile_session_value_preference,
    set_theme_preference,
    set_value_preference,
)
from app.crud.auth.session import (
    create_session_by_userid,
    get_session_theme_preference,
    get_session_value_preference,
    insert_session_by_userid,
    delete_session,
    set_session_theme_preference,
    set_session_value_preference,
)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
logger = logging.getLogger(__name__)

def build_auth_session_response(
    user_id: str | None,
) -> AuthSessionResponse:
    return AuthSessionResponse(
        authenticated=user_id is not None,
        user_id=user_id,
    )


async def register(
    credentials: Login,
    ctx: Context,
) -> AuthSessionResponse:
    db_user = await get_user_by_credentials(credentials, ctx.db)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Username already taken"
        )
    await insert_user(credentials, ctx.db)
    return await login(credentials, ctx)


async def login(
    credentials: Login,
    ctx: Context,
) -> AuthSessionResponse:
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
    await reconcile_session_value_preference(
        user=db_user,
        session=session,
        db=ctx.db,
    )

    return build_auth_session_response(
        str(db_user.id),
    )


async def logout(
    ctx: Context,
) -> AuthSessionResponse:
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
    value_preference = (
        get_session_value_preference(
            ctx.session,
        )
        or get_value_preference(
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

    if value_preference is not None:
        await set_session_value_preference(
            session=new_session,
            value_preference=value_preference,
            db=ctx.db,
        )

    return build_auth_session_response(
        None,
    )


async def update_theme(
    body: ThemePreferenceUpdate,
    ctx: Context,
) -> ThemePreferenceResponse:
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
        return ThemePreferenceResponse(
            theme_preference=(
                user.settings.get("theme_preference")
            ),
        )

    return ThemePreferenceResponse(
        theme_preference=(
            session.settings.get("theme_preference")
        ),
    )


async def update_value_preference(
    body: ValuePreferenceUpdate,
    ctx: Context,
) -> ValuePreferenceResponse:
    session = await set_session_value_preference(
        session=ctx.session,
        value_preference=body.value_preference,
        db=ctx.db,
    )

    if ctx.site_user:
        user = await set_value_preference(
            user=ctx.site_user,
            value_preference=body.value_preference,
            db=ctx.db,
        )
        return ValuePreferenceResponse(
            value_preference=get_value_preference(
                user,
            ),
        )

    return ValuePreferenceResponse(
        value_preference=get_session_value_preference(
            session,
        ),
    )
