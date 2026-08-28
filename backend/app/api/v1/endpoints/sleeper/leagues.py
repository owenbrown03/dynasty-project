from fastapi import APIRouter, BackgroundTasks, Query, Request

from app.api.cancellation import cancel_on_disconnect
from app.api.deps import ContextDep
from app.crud.auth.session import (
    get_session_draft_pick_projection_settings,
)
from app.crud.auth.user import (
    get_draft_pick_projection_settings,
)
from app.services.dashboard.service import (
    get_user_dashboard,
    _prefetch_trade_signals,
)
from app.schemas.league import (
    LeagueOverviewItem,
    LeagueSelectorItem,
    LeagueVisibilityItem,
    LeagueFocusItem,
    LeagueFocusUpdate,
    LeagueVisibilityUpdate,
    UserLeagueNoteUpdate,
    UserLeagueNoteResponse,
)
from app.services.leagues.details import LeagueDetails
from app.services.leagues.overview import (
    get_league_overview,
    get_league_selector_options,
)
from app.services.leagues.visibility import (
    set_league_focus,
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

@router.get(
    "/selector/{username}",
    response_model=list[LeagueSelectorItem],
)
async def selector_endpoint(
    username: str,
    ctx: ContextDep,
    include_hidden: bool = Query(default=False),
):
    return await get_league_selector_options(
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
    request: Request,
    league_id: str,
    ctx: ContextDep,
    cheap: bool = False,
):
    async with cancel_on_disconnect(request):
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
            cheap=cheap,
        )

@router.get("/dashboard/{username}")
async def dashboard_endpoint(
    request: Request,
    username: str,
    ctx: ContextDep,
    background_tasks: BackgroundTasks,
    cheap: bool = False,
):
    async with cancel_on_disconnect(request):
        site_user_id = (
            ctx.site_user.id
            if ctx.site_user is not None
            else None
        )
        result = await get_user_dashboard(
            ctx.db,
            ctx.redis,
            ctx.sleeper,
            username,
            site_user_id=site_user_id,
            cheap=cheap,
        )
        background_tasks.add_task(
            _prefetch_trade_signals,
            username,
            site_user_id,
        )
        return result


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


@router.put(
    "/focus/{league_id}",
    response_model=LeagueFocusItem,
)
async def focus_endpoint(
    league_id: str,
    body: LeagueFocusUpdate,
    ctx: ContextDep,
):
    return await set_league_focus(
        ctx=ctx,
        league_id=league_id,
        focused=body.focused,
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
