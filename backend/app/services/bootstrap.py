from fastapi import APIRouter
from sqlmodel import select

from app.core.context import Context
from app.crud.auth.session import (
    get_session_accent_color,
    get_session_draft_pick_projection_settings,
    get_session_theme_preference,
    get_session_value_preference,
    get_session_war_value_settings,
)
from app.crud.auth.user import (
    get_accent_color,
    get_draft_pick_projection_settings,
    is_email_verified,
    get_theme_preference,
    get_value_preference,
    get_war_value_settings,
)
from app.models.db.sleeper.api import User as SleeperUser
from app.schemas.bootstrap import (
    BootstrapResponse,
    BootstrapUser,
    BootstrapSleeper,
)

router = APIRouter()

async def bootstrap(ctx: Context):

    site_user = None
    sleeper_avatar = None

    if ctx.site_user:
        site_user = BootstrapUser(
            id=str(ctx.site_user.id),
            email=ctx.site_user.email,
            email_verified=is_email_verified(
                ctx.site_user,
            ),
            verification_email_sent_at=(
                ctx.site_user.verification_email_sent_at
            ),
        )

    if ctx.connection and ctx.connection.sleeper_user_id:
        result = await ctx.db.execute(
            select(SleeperUser.avatar).where(
                SleeperUser.user_id == ctx.connection.sleeper_user_id,
            )
        )
        sleeper_avatar = result.scalar_one_or_none()

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
        sleeper_avatar=sleeper_avatar,
        can_read=ctx.connection is not None,
        can_write=ctx.can_write,
    )

    return BootstrapResponse(
        authenticated=ctx.site_user is not None,
        site_user=site_user,
        sleeper=sleeper,
        theme_preference=(
            get_theme_preference(
                ctx.site_user,
            )
            if ctx.site_user
            else get_session_theme_preference(
                ctx.session,
            )
        ),
        accent_color=(
            get_accent_color(
                ctx.site_user,
            )
            if ctx.site_user
            else get_session_accent_color(
                ctx.session,
            )
        ),
        value_preference=(
            get_value_preference(
                ctx.site_user,
            )
            if ctx.site_user
            else get_session_value_preference(
                ctx.session,
            )
        ),
        war_value_settings=(
            get_war_value_settings(
                ctx.site_user,
            )
            if ctx.site_user
            else get_session_war_value_settings(
                ctx.session,
            )
        ),
        draft_pick_projection_settings=(
            get_draft_pick_projection_settings(
                ctx.site_user,
            )
            if ctx.site_user
            else get_session_draft_pick_projection_settings(
                ctx.session,
            )
        ),
    )
