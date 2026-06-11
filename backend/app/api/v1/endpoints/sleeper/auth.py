from fastapi import APIRouter, Depends

from app.schemas.sleeper import auth
from app.core.context import Context
from app.api.deps import get_context
from app.services.sleeper.auth import send_code, verify_code

router = APIRouter()

@router.post("/send-code")
async def send_code_endpoint(
    body: auth.SendCodeRequest,
    ctx: Context = Depends(get_context),
):
    return await send_code(body, ctx)

@router.post("/verify-code")
async def verify_code_endpoint(
    body: auth.VerifyCodeRequest,
    ctx: Context = Depends(get_context),
):
    return await verify_code(body, ctx)