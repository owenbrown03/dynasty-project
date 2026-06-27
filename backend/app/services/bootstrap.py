from fastapi import APIRouter

from app.core.context import Context
from app.schemas.bootstrap import (
    BootstrapResponse,
    BootstrapUser,
    BootstrapSleeper,
)

router = APIRouter()

async def bootstrap(ctx: Context):

    site_user = None

    if ctx.site_user:
        site_user = BootstrapUser(
            id=str(ctx.site_user.id),
            email=ctx.site_user.email,
        )

    sleeper = BootstrapSleeper(
        linked=ctx.connection is not None,
        sleeper_username=(
            ctx.connection.sleeper_username
            if ctx.connection else None
        ),
        sleeper_user_id=(
            ctx.connection.sleeper_user_id
            if ctx.connection else None
        ),
        can_read=ctx.connection is not None,
        can_write=ctx.can_write,
    )

    return BootstrapResponse(
        authenticated=ctx.site_user is not None,
        site_user=site_user,
        sleeper=sleeper,
    )