from app.core.broker import broker
from app.services.sync.external import run_daily_external_syncs


@broker.task
async def run_daily_external_syncs_task(
    force: bool = False,
):
    return await run_daily_external_syncs(
        force=force,
    )
