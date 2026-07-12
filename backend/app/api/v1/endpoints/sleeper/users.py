from fastapi import APIRouter, Query

from app.api.deps import ContextDep
from app.crud.sleeper.roster import get_user_rosters, get_user_orphans
from app.schemas.commissioner import (
    CommissionerLeagueDuesEntry,
    CommissionerLeagueDuesUpdate,
    CommissionerLeagueNoteUpdate,
    CommissionerLeagueSettingsUpdate,
    CommissionerOrphansResponse,
    CommissionerWorkspaceLeague,
    CommissionerWorkspaceResponse,
)
from app.schemas.finance import (
    FinanceDefaultsUpdate,
    FinanceLeagueDefaultsUpdate,
    FinanceLeagueSeasonEntry,
    FinanceSeasonReset,
    FinanceLeagueSeasonUpdate,
    FinanceSummaryResponse,
)
from app.schemas.reminders import (
    ReminderCreate,
    ReminderDelete,
    ReminderItem,
    ReminderListResponse,
    ReminderTestSendResponse,
    ReminderUpdate,
)
from app.services.commissioner.orphans import get_commissioner_orphans
from app.services.commissioner.workspace import (
    get_commissioner_workspace,
    save_commissioner_dues,
    save_commissioner_note,
    save_commissioner_settings,
)
from app.services.finance import (
    get_finance_summary,
    reset_finance_entry,
    save_finance_defaults,
    save_finance_entry,
    save_finance_league_defaults,
)
from app.services.reminders import (
    create_reminder,
    list_reminders,
    remove_reminder,
    save_reminder,
    send_test_reminder,
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


@router.post(
    "/commissioner/workspace/settings",
    response_model=CommissionerWorkspaceLeague,
)
async def save_commissioner_settings_endpoint(
    body: CommissionerLeagueSettingsUpdate,
    ctx: ContextDep,
):
    return await save_commissioner_settings(
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
    "/finance/defaults",
    response_model=FinanceSummaryResponse,
)
async def save_finance_defaults_endpoint(
    body: FinanceDefaultsUpdate,
    ctx: ContextDep,
):
    return await save_finance_defaults(
        body,
        ctx,
    )


@router.post(
    "/finance/defaults/leagues",
    response_model=FinanceSummaryResponse,
)
async def save_finance_league_defaults_endpoint(
    body: FinanceLeagueDefaultsUpdate,
    ctx: ContextDep,
):
    return await save_finance_league_defaults(
        body,
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


@router.post(
    "/finance/season/reset",
    response_model=FinanceLeagueSeasonEntry,
)
async def reset_finance_entry_endpoint(
    body: FinanceSeasonReset,
    ctx: ContextDep,
):
    return await reset_finance_entry(
        body,
        ctx,
    )


@router.get(
    "/reminders",
    response_model=ReminderListResponse,
)
async def get_reminders_endpoint(
    ctx: ContextDep,
):
    return await list_reminders(
        ctx,
    )


@router.post(
    "/reminders",
    response_model=ReminderItem,
)
async def create_reminder_endpoint(
    body: ReminderCreate,
    ctx: ContextDep,
):
    return await create_reminder(
        body,
        ctx,
    )


@router.post(
    "/reminders/update",
    response_model=ReminderItem,
)
async def save_reminder_endpoint(
    body: ReminderUpdate,
    ctx: ContextDep,
):
    return await save_reminder(
        body,
        ctx,
    )


@router.post(
    "/reminders/delete",
)
async def delete_reminder_endpoint(
    body: ReminderDelete,
    ctx: ContextDep,
):
    await remove_reminder(
        body,
        ctx,
    )
    return {"status": "deleted"}


@router.post(
    "/reminders/test-send",
    response_model=ReminderTestSendResponse,
)
async def test_send_reminder_endpoint(
    body: ReminderDelete,
    ctx: ContextDep,
):
    return await send_test_reminder(
        body,
        ctx,
    )
