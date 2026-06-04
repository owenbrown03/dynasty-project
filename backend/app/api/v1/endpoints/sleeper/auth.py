from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.sleeper import auth
from app.integrations.sleeper.client import SleeperClientManager
from app.models.auth import UserSession, SiteUser
from app.crud.sleeper.connection import upsert_sleeper_connection
from app.api.deps import get_db, get_current_session, get_current_user

router = APIRouter()

@router.post("/send-code")
async def send_code_endpoint(
    body: auth.SendCodeRequest,
):
    sleeper = SleeperClientManager.get()

    return await sleeper.auth_api.send_code(
        username=body.username,
        captcha=body.captcha,
    )

@router.post("/verify-code")
async def verify_code_endpoint(
    body: auth.VerifyCodeRequest,
    user: SiteUser = Depends(get_current_session),
    session: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sleeper = SleeperClientManager.get()

    token = await sleeper.auth_api.verify_code(
        username=body.username,
        code=body.code,
        captcha=body.captcha,
    )

    return await upsert_sleeper_connection(
        db=db,
        sleeper=sleeper,
        user=user,
        session=session,
        token=token,
    )