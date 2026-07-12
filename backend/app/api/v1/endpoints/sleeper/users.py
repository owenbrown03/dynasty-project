from fastapi import APIRouter, Query

from app.api.deps import ContextDep
from app.crud.sleeper.roster import get_user_rosters, get_user_orphans
from app.schemas.commissioner import (
    CommissionerLeagueDuesEntry,
    CommissionerLeagueDuesUpdate,
    CommissionerLeagueNoteUpdate,
    CommissionerOrphansResponse,
    CommissionerWorkspaceLeague,
    CommissionerWorkspaceResponse,
)
from app.schemas.finance import (
    FinanceLeagueSeasonEntry,
    FinanceLeagueSeasonUpdate,
    FinanceSummaryResponse,
)
from app.services.commissioner.orphans import get_commissioner_orphans
from app.services.commissioner.workspace import (
    get_commissioner_workspace,
    save_commissioner_dues,
    save_commissioner_note,
)
from app.services.finance import (
    get_finance_summary,
    save_finance_entry,
)
from app.services.values.basis import ValueBasis
from app.tasks.user import sync_user_data_task

router = APIRouter()

@router.post("/{username}/sync")
async def sync_user_data_endpoint(
    username: str,
):
    await sync_user_data_task.kiq(username)
    return {"status": "sync_initiated"}

@router.get("/{username}/rosters")
async def get_user_rosters_endpoint(
    username: str, 
    ctx: ContextDep,
):
    return await get_user_rosters(ctx.db, ctx.sleeper, username)

@router.get("/{username}/orphans")
async def get_user_orphans_endpoint(
    username: str,
    ctx: ContextDep,
):
    return await get_user_orphans(ctx.db, ctx.sleeper, username)


@router.get(
    "/{username}/commissioner/orphans",
    response_model=CommissionerOrphansResponse,
)
async def get_commissioner_orphans_endpoint(
    username: str,
    ctx: ContextDep,
    value_basis: ValueBasis = Query(
        ValueBasis.FANTASYCALC,
    ),
):
    return await get_commissioner_orphans(
        db=ctx.db,
        username=username,
        value_basis=value_basis,
    )


@router.get(
    "/commissioner/workspace",
    response_model=CommissionerWorkspaceResponse,
)
async def get_commissioner_workspace_endpoint(
    ctx: ContextDep,
):
    return await get_commissioner_workspace(
        ctx,
    )


@router.post(
    "/commissioner/workspace/note",
    response_model=CommissionerWorkspaceLeague,
)
async def save_commissioner_note_endpoint(
    body: CommissionerLeagueNoteUpdate,
    ctx: ContextDep,
):
    return await save_commissioner_note(
        body,
        ctx,
    )


@router.post(
    "/commissioner/workspace/dues",
    response_model=CommissionerLeagueDuesEntry,
)
async def save_commissioner_dues_endpoint(
    body: CommissionerLeagueDuesUpdate,
    ctx: ContextDep,
):
    return await save_commissioner_dues(
        body,
        ctx,
    )


@router.get(
    "/finance/summary",
    response_model=FinanceSummaryResponse,
)
async def get_finance_summary_endpoint(
    ctx: ContextDep,
):
    return await get_finance_summary(
        ctx,
    )


@router.post(
    "/finance/season",
    response_model=FinanceLeagueSeasonEntry,
)
async def save_finance_entry_endpoint(
    body: FinanceLeagueSeasonUpdate,
    ctx: ContextDep,
):
    return await save_finance_entry(
        body,
        ctx,
    )
