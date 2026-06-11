from fastapi import APIRouter, Depends

from app.schemas.auth import Login
from app.core.context import Context
from app.api.deps import get_context
from app.services.auth import register, login, logout, validate, me

router = APIRouter()

@router.post("/register")
async def register_endpoint(
    credentials: Login,
    ctx: Context = Depends(get_context),
):
    await register(credentials, ctx)
    await login(credentials, ctx)

@router.post("/login")
async def login_endpoint(
    credentials: Login,
    ctx: Context = Depends(get_context),
):
    await login(credentials, ctx)

@router.post("/logout")
async def logout_endpoint(
    ctx: Context = Depends(get_context),
):
    await logout(ctx)

@router.get("/validate")
async def validate_endpoint(
    ctx: Context = Depends(get_context),
):
    return await validate(ctx)

@router.get("/me")
async def me_endpoint(
    ctx: Context = Depends(get_context),
):
    return await me(ctx)