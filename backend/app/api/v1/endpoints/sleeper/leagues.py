from fastapi import APIRouter, Query

from app.api.deps import ContextDep
from app.crud.auth.session import (
    get_session_draft_pick_projection_settings,
)
from app.crud.auth.user import (
    get_draft_pick_projection_settings,
)
from app.services.dashboard.service import get_user_dashboard
from app.schemas.league import (
    LeagueOverviewItem,
    LeagueVisibilityItem,
    LeagueVisibilityUpdate,
    UserLeagueNoteUpdate,
    UserLeagueNoteResponse,
)
from app.services.leagues.details import LeagueDetails
from app.services.leagues.overview import get_league_overview
from app.services.leagues.visibility import (
    set_league_visibility,
)
from app.services.leagues.notes import save_user_note

router = APIRouter()

@router.get(
    "/overview/{username}",
    response_model=list[LeagueOverviewItem],
)
async def overview_endpoint(
    username: str,
    ctx: ContextDep,
    include_hidden: bool = Query(default=False),
):
    return await get_league_overview(
        ctx.db,
        username=username,
        site_user_id=(
            ctx.site_user.id
            if ctx.site_user is not None
            else None
        ),
        include_hidden=include_hidden,
    )

@router.get("/details/{league_id}")
async def details_endpoint(
    league_id: str,
    ctx: ContextDep,
):
    return await LeagueDetails().get_league_details(
        ctx.db,
        ctx.redis,
        league_id=league_id,
        site_user_id=(
            ctx.site_user.id
            if ctx.site_user is not None
            else None
        ),
        draft_pick_projection_settings=(
            get_draft_pick_projection_settings(
                ctx.site_user,
            )
            if ctx.site_user is not None
            else get_session_draft_pick_projection_settings(
                ctx.session,
            )
        ),
    )

@router.get("/dashboard/{username}")
async def dashboard_endpoint(
    username: str,
    ctx: ContextDep,
):
    return await get_user_dashboard(
        ctx.db,
        ctx.redis,
        ctx.sleeper,
        username,
        site_user_id=(
            ctx.site_user.id
            if ctx.site_user is not None
            else None
        ),
    )


@router.put(
    "/visibility/{league_id}",
    response_model=LeagueVisibilityItem,
)
async def visibility_endpoint(
    league_id: str,
    body: LeagueVisibilityUpdate,
    ctx: ContextDep,
):
    return await set_league_visibility(
        ctx=ctx,
        league_id=league_id,
        hidden=body.hidden,
    )


@router.post(
    "/note",
    response_model=UserLeagueNoteResponse,
)
async def save_user_note_endpoint(
    body: UserLeagueNoteUpdate,
    ctx: ContextDep,
):
    return await save_user_note(
        ctx=ctx,
        league_id=body.league_id,
        note=body.note,
    )
