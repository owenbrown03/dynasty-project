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
    CommissionerCutdownLeague,
    CommissionerCutdownActionRequest,
    CommissionerCutdownActionResponse,
    CommissionerPollBroadcastRequest,
    CommissionerPollBroadcastResponse,
    CommissionerFaabLeagueInfo,
    CommissionerFaabResetRequest,
    CommissionerFaabResetResponse,
    CommissionerWaiverLeagueInfo,
    CommissionerWaiverUpdateRequest,
    CommissionerWaiverUpdateResponse,
    CommissionerStandardWaiverPreset,
    CommissionerStandardWaiverPresetUpdate,
    CommissionerLeagueSettingsInfo,
    CommissionerSettingsUpdateRequest,
    CommissionerSettingsUpdateResponse,
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
from app.services.commissioner.cutdowns import (
    get_commissioner_cutdown_violations,
    execute_cutdown_action,
)
from app.services.commissioner.faab import (
    get_commissioner_faab_overview,
    reset_commissioner_faab,
)
from app.services.commissioner.waivers import (
    get_commissioner_waivers_overview,
    update_commissioner_waivers,
    get_commissioner_standard_waiver_preset,
    save_commissioner_standard_waiver_preset,
    reset_commissioner_standard_waiver_preset,
)
from app.services.commissioner.general_settings import (
    get_commissioner_settings_overview,
    update_commissioner_settings,
)
from app.services.commissioner.polls import broadcast_commissioner_poll
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
from app.tasks.trade import sync_leaguemates_task

router = APIRouter()

@router.post("/{username}/sync")
async def sync_user_data_endpoint(
    username: str,
):
    await sync_user_data_task.kiq(username)
    await sync_leaguemates_task.kiq(username, force=True)
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
        redis=ctx.redis,
        username=username,
        value_basis=value_basis,
        site_user_id=ctx.site_user.id if ctx.site_user else None,
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


@router.post(
    "/commissioner/polls/broadcast",
    response_model=CommissionerPollBroadcastResponse,
)
async def broadcast_commissioner_poll_endpoint(
    body: CommissionerPollBroadcastRequest,
    ctx: ContextDep,
):
    return await broadcast_commissioner_poll(
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

@router.get(
    "/commissioner/faab",
    response_model=list[CommissionerFaabLeagueInfo],
)
async def get_commissioner_faab_endpoint(
    ctx: ContextDep,
):
    return await get_commissioner_faab_overview(ctx)

@router.post(
    "/commissioner/faab/reset",
    response_model=CommissionerFaabResetResponse,
)
async def reset_commissioner_faab_endpoint(
    body: CommissionerFaabResetRequest,
    ctx: ContextDep,
):
    return await reset_commissioner_faab(ctx, body)

@router.get(
    "/commissioner/cutdowns",
    response_model=list[CommissionerCutdownLeague],
)
async def get_commissioner_cutdowns_endpoint(
    ctx: ContextDep,
):
    return await get_commissioner_cutdown_violations(ctx)

@router.post(
    "/commissioner/cutdowns/action",
    response_model=CommissionerCutdownActionResponse,
)
async def execute_commissioner_cutdowns_action_endpoint(
    body: CommissionerCutdownActionRequest,
    ctx: ContextDep,
):
    return await execute_cutdown_action(body, ctx)

@router.get(
    "/commissioner/waivers",
    response_model=list[CommissionerWaiverLeagueInfo],
)
async def get_commissioner_waivers_endpoint(
    ctx: ContextDep,
):
    return await get_commissioner_waivers_overview(ctx)

@router.post(
    "/commissioner/waivers/update",
    response_model=CommissionerWaiverUpdateResponse,
)
async def update_commissioner_waivers_endpoint(
    body: CommissionerWaiverUpdateRequest,
    ctx: ContextDep,
):
    return await update_commissioner_waivers(ctx, body)


@router.get(
    "/commissioner/waivers/preset",
    response_model=CommissionerStandardWaiverPreset,
)
async def get_commissioner_waivers_preset_endpoint(
    ctx: ContextDep,
    preset_type: str = Query("inseason", description="Preset type: 'inseason' or 'offseason'"),
):
    return await get_commissioner_standard_waiver_preset(ctx, preset_type=preset_type)


@router.post(
    "/commissioner/waivers/preset",
    response_model=CommissionerStandardWaiverPreset,
)
async def save_commissioner_waivers_preset_endpoint(
    body: CommissionerStandardWaiverPresetUpdate,
    ctx: ContextDep,
    preset_type: str = Query("inseason", description="Preset type: 'inseason' or 'offseason'"),
):
    return await save_commissioner_standard_waiver_preset(ctx, body, preset_type=preset_type)


@router.post(
    "/commissioner/waivers/preset/reset",
    response_model=CommissionerStandardWaiverPreset,
)
async def reset_commissioner_waivers_preset_endpoint(
    ctx: ContextDep,
    preset_type: str = Query("inseason", description="Preset type: 'inseason' or 'offseason'"),
):
    return await reset_commissioner_standard_waiver_preset(ctx, preset_type=preset_type)


@router.get(
    "/commissioner/settings",
    response_model=list[CommissionerLeagueSettingsInfo],
)
async def get_commissioner_settings_endpoint(
    ctx: ContextDep,
):
    return await get_commissioner_settings_overview(ctx)


@router.post(
    "/commissioner/settings/update",
    response_model=CommissionerSettingsUpdateResponse,
)
async def update_commissioner_settings_endpoint(
    body: CommissionerSettingsUpdateRequest,
    ctx: ContextDep,
):
    return await update_commissioner_settings(ctx, body)



