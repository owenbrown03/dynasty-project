from fastapi import APIRouter

from app.api.deps import ContextDep
from app.integrations.sleeper.schemas import auth
from app.services.sleeper.auth import send_code, verify_code

router = APIRouter()

@router.post("/send-code")
async def send_code_endpoint(
    body: auth.SendCodeRequest,
    ctx: ContextDep,
):
    return await send_code(body, ctx)

@router.post("/verify-code")
async def verify_code_endpoint(
    body: auth.VerifyCodeRequest,
    ctx: ContextDep,
):
    return await verify_code(body, ctx)
