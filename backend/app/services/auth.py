import logging
from datetime import datetime

from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.schemas.auth import (
    AccentColorResponse,
    AccentColorUpdate,
    AuthSessionResponse,
    DraftPickProjectionSettingsResponse,
    DraftPickProjectionSettingsUpdate,
    FinanceProjectionSettingsResponse,
    FinanceProjectionSettingsUpdate,
    EmailVerificationConfirmRequest,
    EmailVerificationRequestResponse,
    EmailVerificationStatusResponse,
    Login,
    ThemePreferenceResponse,
    ThemePreferenceUpdate,
    ValuePreferenceResponse,
    ValuePreferenceUpdate,
    WarValueSettingsResponse,
    WarValueSettingsUpdate,
)
from app.core.context import Context
from app.crud.auth.user import (
    consume_email_verification,
    create_email_verification_token,
    get_accent_color,
    get_draft_pick_projection_settings,
    get_email_verification_by_token,
    get_finance_projection_settings,
    get_theme_preference,
    get_value_preference,
    get_war_value_settings,
    get_user_by_credentials,
    is_email_verified,
    insert_user,
    reconcile_session_accent_color,
    reconcile_session_theme_preference,
    reconcile_session_draft_pick_projection_settings,
    reconcile_session_finance_projection_settings,
    reconcile_session_value_preference,
    reconcile_session_war_value_settings,
    set_accent_color,
    set_draft_pick_projection_settings,
    set_finance_projection_settings,
    set_theme_preference,
    set_value_preference,
    set_war_value_settings,
)
from app.crud.auth.session import (
    create_session_by_userid,
    get_session_accent_color,
    get_session_draft_pick_projection_settings,
    get_session_finance_projection_settings,
    get_session_theme_preference,
    get_session_value_preference,
    get_session_war_value_settings,
    insert_session_by_userid,
    delete_session,
    set_session_accent_color,
    set_session_draft_pick_projection_settings,
    set_session_finance_projection_settings,
    set_session_theme_preference,
    set_session_value_preference,
    set_session_war_value_settings,
)
from app.models.db.auth import SiteUser
from app.services.email import (
    send_email_verification_message,
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
    db_user = await insert_user(credentials, ctx.db)
    await request_email_verification(
        ctx=ctx,
        user=db_user,
    )
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
    await reconcile_session_draft_pick_projection_settings(
        user=db_user,
        session=session,
        db=ctx.db,
    )
    await reconcile_session_finance_projection_settings(
        user=db_user,
        session=session,
        db=ctx.db,
    )
    await reconcile_session_value_preference(
        user=db_user,
        session=session,
        db=ctx.db,
    )
    await reconcile_session_war_value_settings(
        user=db_user,
        session=session,
        db=ctx.db,
    )
    await reconcile_session_accent_color(
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
    draft_pick_projection_settings = (
        get_session_draft_pick_projection_settings(
            ctx.session,
        )
        or get_draft_pick_projection_settings(
            ctx.site_user,
        )
    )
    war_value_settings = (
        get_session_war_value_settings(
            ctx.session,
        )
        or get_war_value_settings(
            ctx.site_user,
        )
    )
    finance_projection_settings = (
        get_session_finance_projection_settings(
            ctx.session,
        )
        or get_finance_projection_settings(
            ctx.site_user,
        )
    )
    accent_color = (
        get_session_accent_color(
            ctx.session,
        )
        or get_accent_color(
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

    await set_session_draft_pick_projection_settings(
        session=new_session,
        draft_pick_projection_settings=(
            draft_pick_projection_settings
        ),
        db=ctx.db,
    )
    await set_session_finance_projection_settings(
        session=new_session,
        finance_projection_settings=(
            finance_projection_settings
        ),
        db=ctx.db,
    )
    await set_session_war_value_settings(
        session=new_session,
        war_value_settings=war_value_settings,
        db=ctx.db,
    )

    if accent_color is not None:
        await set_session_accent_color(
            session=new_session,
            accent_color=accent_color,
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


async def update_accent_color(
    body: AccentColorUpdate,
    ctx: Context,
) -> AccentColorResponse:
    session = await set_session_accent_color(
        session=ctx.session,
        accent_color=body.accent_color,
        db=ctx.db,
    )

    if ctx.site_user:
        user = await set_accent_color(
            user=ctx.site_user,
            accent_color=body.accent_color,
            db=ctx.db,
        )
        return AccentColorResponse(
            accent_color=get_accent_color(user),
        )

    return AccentColorResponse(
        accent_color=get_session_accent_color(session),
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


async def update_draft_pick_projection_settings(
    body: DraftPickProjectionSettingsUpdate,
    ctx: Context,
) -> DraftPickProjectionSettingsResponse:
    session = await set_session_draft_pick_projection_settings(
        session=ctx.session,
        draft_pick_projection_settings=(
            body.settings.model_dump()
        ),
        db=ctx.db,
    )

    if ctx.site_user:
        user = await set_draft_pick_projection_settings(
            user=ctx.site_user,
            draft_pick_projection_settings=(
                body.settings.model_dump()
            ),
            db=ctx.db,
        )
        return DraftPickProjectionSettingsResponse(
            settings=get_draft_pick_projection_settings(
                user,
            ),
        )

    return DraftPickProjectionSettingsResponse(
        settings=get_session_draft_pick_projection_settings(
            session,
        ),
    )


async def update_finance_projection_settings(
    body: FinanceProjectionSettingsUpdate,
    ctx: Context,
) -> FinanceProjectionSettingsResponse:
    session = await set_session_finance_projection_settings(
        session=ctx.session,
        finance_projection_settings=(
            body.settings.model_dump()
        ),
        db=ctx.db,
    )

    if ctx.site_user:
        user = await set_finance_projection_settings(
            user=ctx.site_user,
            finance_projection_settings=(
                body.settings.model_dump()
            ),
            db=ctx.db,
        )
        return FinanceProjectionSettingsResponse(
            settings=get_finance_projection_settings(
                user,
            ),
        )

    return FinanceProjectionSettingsResponse(
        settings=get_session_finance_projection_settings(
            session,
        ),
    )


async def update_war_value_settings(
    body: WarValueSettingsUpdate,
    ctx: Context,
) -> WarValueSettingsResponse:
    settings_payload = body.settings.model_dump()
    session = await set_session_war_value_settings(
        session=ctx.session,
        war_value_settings=settings_payload,
        db=ctx.db,
    )

    if ctx.site_user:
        user = await set_war_value_settings(
            user=ctx.site_user,
            war_value_settings=settings_payload,
            db=ctx.db,
        )
        return WarValueSettingsResponse(
            settings=get_war_value_settings(
                user,
            ),
        )

    return WarValueSettingsResponse(
        settings=get_session_war_value_settings(
            session,
        ),
    )


async def request_email_verification(
    *,
    ctx: Context,
    user=None,
) -> EmailVerificationRequestResponse:
    db_user = user or ctx.site_user

    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    if is_email_verified(db_user):
        return EmailVerificationRequestResponse(
            email_verified=True,
            verification_email_sent_at=(
                db_user.verification_email_sent_at
            ),
            delivery="log",
            verification_url=None,
        )

    _, raw_token = await create_email_verification_token(
        user=db_user,
        db=ctx.db,
    )

    delivery, verification_url = send_email_verification_message(
        recipient=db_user.email,
        token=raw_token,
    )

    return EmailVerificationRequestResponse(
        email_verified=False,
        verification_email_sent_at=(
            db_user.verification_email_sent_at
        ),
        delivery=delivery,
        verification_url=(
            verification_url
            if delivery == "log"
            else None
        ),
    )


async def verify_email(
    body: EmailVerificationConfirmRequest,
    ctx: Context,
) -> EmailVerificationStatusResponse:
    verification = await get_email_verification_by_token(
        token=body.token,
        db=ctx.db,
    )

    if verification is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )

    now = datetime.utcnow()

    if verification.consumed_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token already used",
        )

    if verification.expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token expired",
        )

    db_user = await ctx.db.get(
        SiteUser,
        verification.site_user_id,
    )

    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found for verification token",
        )

    updated_user = await consume_email_verification(
        verification=verification,
        user=db_user,
        db=ctx.db,
    )

    return EmailVerificationStatusResponse(
        email_verified=is_email_verified(
            updated_user,
        ),
        verification_email_sent_at=(
            updated_user.verification_email_sent_at
        ),
    )
