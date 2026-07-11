from fastapi import APIRouter

from app.api.deps import ContextDep
from app.schemas.auth import Login, ThemePreferenceUpdate
from app.services.auth import register, login, logout, validate, me, update_theme

router = APIRouter()

@router.post("/register")
async def register_endpoint(
    credentials: Login,
    ctx: ContextDep,
):
    await register(credentials, ctx)
    await login(credentials, ctx)

@router.post("/login")
async def login_endpoint(
    credentials: Login,
    ctx: ContextDep,
):
    await login(credentials, ctx)

@router.post("/logout")
async def logout_endpoint(
    ctx: ContextDep,
):
    await logout(ctx)


@router.post("/theme")
async def update_theme_endpoint(
    body: ThemePreferenceUpdate,
    ctx: ContextDep,
):
    return await update_theme(body, ctx)
