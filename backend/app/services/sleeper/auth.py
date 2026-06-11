import uuid
from fastapi import HTTPException, status

from app.schemas.sleeper import auth
from app.core.context import Context
from app.integrations.sleeper.exceptions import (
    SleeperGraphQLError,
    SleeperAuthError,
)
from app.services.sleeper.connection import upsert
from app.services.sleeper.pending import (
    store_pending,
    pop_pending,
)


async def send_code(
    body: auth.SendCodeRequest,
    ctx: Context,
):
    try:
        await ctx.sleeper.write.send_code(
            username=body.username,
            captcha=body.captcha,
        )

    except SleeperGraphQLError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    connect_id = str(uuid.uuid4())

    await store_pending(
        ctx,
        connect_id,
        body.username,
    )

    return auth.SendCodeResponse(
        connect_id=connect_id,
    )


async def verify_code(
    body: auth.VerifyCodeRequest,
    ctx: Context,
):
    connect_id = await pop_pending(
        ctx,
        body.connect_id,
    )

    if not connect_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="connect_id not found or expired. Start again from /connect.",
        )

    try:
        token = await ctx.sleeper.write.verify_code(
            username=connect_id,
            code=body.code.strip(),
            captcha=body.captcha,
        )

    except SleeperAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    except SleeperGraphQLError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    await upsert(
        ctx=ctx,
        token=token,
    )

    return auth.VerifyCodeResponse(
        sleeper_token=token,
    )