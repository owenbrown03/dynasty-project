from fastapi import APIRouter

from app.api.deps import ContextDep
from app.schemas.auth import (
    AuthSessionResponse,
    Login,
    ThemePreferenceResponse,
    ThemePreferenceUpdate,
)
from app.services.auth import (
    login,
    logout,
    register,
    update_theme,
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
    "/theme",
    response_model=ThemePreferenceResponse,
)
async def update_theme_endpoint(
    body: ThemePreferenceUpdate,
    ctx: ContextDep,
):
    return await update_theme(body, ctx)
