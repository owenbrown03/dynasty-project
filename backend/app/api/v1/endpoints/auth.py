from fastapi import APIRouter

from app.api.deps import ContextDep
from app.schemas.auth import (
    AuthSessionResponse,
    EmailVerificationConfirmRequest,
    EmailVerificationRequestResponse,
    EmailVerificationStatusResponse,
    Login,
    ThemePreferenceResponse,
    ThemePreferenceUpdate,
    ValuePreferenceResponse,
    ValuePreferenceUpdate,
)
from app.services.auth import (
    login,
    logout,
    request_email_verification,
    register,
    update_theme,
    update_value_preference,
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
    "/value",
    response_model=ValuePreferenceResponse,
)
async def update_value_preference_endpoint(
    body: ValuePreferenceUpdate,
    ctx: ContextDep,
):
    return await update_value_preference(body, ctx)
