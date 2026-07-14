from fastapi import APIRouter

from app.api.deps import ContextDep
from app.schemas.auth import (
    AccentColorResponse,
    AccentColorUpdate,
    AuthSessionResponse,
    DraftPickProjectionSettingsResponse,
    DraftPickProjectionSettingsUpdate,
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
from app.services.auth import (
    login,
    logout,
    request_email_verification,
    register,
    update_accent_color,
    update_theme,
    update_draft_pick_projection_settings,
    update_value_preference,
    update_war_value_settings,
    verify_email,
)

router = APIRouter()

@router.post(
    "/register",
    response_model=AuthSessionResponse,
)
async def register_endpoint(
    credentials: Login,
    ctx: ContextDep,
):
    return await register(credentials, ctx)

@router.post(
    "/login",
    response_model=AuthSessionResponse,
)
async def login_endpoint(
    credentials: Login,
    ctx: ContextDep,
):
    return await login(credentials, ctx)

@router.post(
    "/logout",
    response_model=AuthSessionResponse,
)
async def logout_endpoint(
    ctx: ContextDep,
):
    return await logout(ctx)


@router.post(
    "/email/resend",
    response_model=EmailVerificationRequestResponse,
)
async def request_email_verification_endpoint(
    ctx: ContextDep,
):
    return await request_email_verification(
        ctx=ctx,
    )


@router.post(
    "/email/verify",
    response_model=EmailVerificationStatusResponse,
)
async def verify_email_endpoint(
    body: EmailVerificationConfirmRequest,
    ctx: ContextDep,
):
    return await verify_email(body, ctx)


@router.post(
    "/theme",
    response_model=ThemePreferenceResponse,
)
async def update_theme_endpoint(
    body: ThemePreferenceUpdate,
    ctx: ContextDep,
):
    return await update_theme(body, ctx)


@router.post(
    "/accent-color",
    response_model=AccentColorResponse,
)
async def update_accent_color_endpoint(
    body: AccentColorUpdate,
    ctx: ContextDep,
):
    return await update_accent_color(body, ctx)


@router.post(
    "/value",
    response_model=ValuePreferenceResponse,
)
async def update_value_preference_endpoint(
    body: ValuePreferenceUpdate,
    ctx: ContextDep,
):
    return await update_value_preference(body, ctx)


@router.post(
    "/war-value",
    response_model=WarValueSettingsResponse,
)
async def update_war_value_settings_endpoint(
    body: WarValueSettingsUpdate,
    ctx: ContextDep,
):
    return await update_war_value_settings(body, ctx)


@router.post(
    "/draft-pick-projection",
    response_model=DraftPickProjectionSettingsResponse,
)
async def update_draft_pick_projection_settings_endpoint(
    body: DraftPickProjectionSettingsUpdate,
    ctx: ContextDep,
):
    return await update_draft_pick_projection_settings(
        body,
        ctx,
    )
