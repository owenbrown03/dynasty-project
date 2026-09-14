import logging
from typing import Any
from fastapi import HTTPException, status

from app.core.context import Context
from app.crud.sleeper.personal import get_league_sort_orders
from app.services.leagues.selection import (
    get_visible_owned_league_rows_by_sleeper_user_id,
)
from app.schemas.commissioner import (
    CommissionerLeagueSettingsInfo,
    CommissionerSettingsUpdateRequest,
    CommissionerSettingsUpdateResult,
    CommissionerSettingsUpdateResponse,
)

logger = logging.getLogger(__name__)


def _require_commissioner_workspace_context(ctx: Context) -> None:
    if ctx.site_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    if not ctx.connection or not ctx.connection.sleeper_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A linked Sleeper account is required",
        )


async def get_commissioner_settings_overview(
    ctx: Context,
) -> list[CommissionerLeagueSettingsInfo]:
    _require_commissioner_workspace_context(ctx)

    sleeper_user_id = ctx.connection.sleeper_user_id or ""
    owned_rows = await get_visible_owned_league_rows_by_sleeper_user_id(
        db=ctx.db,
        sleeper_user_id=sleeper_user_id,
        site_user_id=ctx.site_user.id,
        include_hidden=False,
    )
    if not owned_rows:
        return []

    # Filter to leagues where the current user is commissioner (roster.is_owner is True)
    commish_rows = [
        row for row in owned_rows
        if row.league and getattr(row.roster, "is_owner", False) is True
    ]

    sort_order = await get_league_sort_orders(
        db=ctx.db,
        user_id=sleeper_user_id,
    )

    overview: list[CommissionerLeagueSettingsInfo] = []
    for row in commish_rows:
        league = row.league
        settings = getattr(league, "settings", {}) or {}

        def _get_int(key: str, default: int) -> int:
            val = settings.get(key)
            if val is None:
                return default
            try:
                return int(val)
            except (ValueError, TypeError):
                return default

        overview.append(
            CommissionerLeagueSettingsInfo(
                league_id=league.league_id,
                league_name=league.name,
                avatar=league.avatar,
                total_rosters=league.total_rosters,
                best_ball=_get_int("best_ball", 0),
                bench_lock=_get_int("bench_lock", 0),
                disable_adds=_get_int("disable_adds", 0),
                offseason_adds=_get_int("offseason_adds", 0),
                disable_trades=_get_int("disable_trades", 0),
                trade_deadline=_get_int("trade_deadline", 11),
                pick_trading=_get_int("pick_trading", 1),
                trade_review_days=_get_int("trade_review_days", 0),
                veto_auto_poll=_get_int("veto_auto_poll", 0),
                veto_show_votes=_get_int("veto_show_votes", 0),
                veto_votes_needed=_get_int("veto_votes_needed", 0),
                playoff_teams=_get_int("playoff_teams", 6),
                playoff_week_start=_get_int("playoff_week_start", 15),
                league_average_match=_get_int("league_average_match", 0),
                waiver_bid_min=_get_int("waiver_bid_min", 0),
                taxi_deadline=_get_int("taxi_deadline", 0),
                taxi_allow_vets=_get_int("taxi_allow_vets", 0),
                taxi_years=_get_int("taxi_years", 0),
                reserve_allow_out=_get_int("reserve_allow_out", 1),
                reserve_allow_doubtful=_get_int("reserve_allow_doubtful", 0),
                reserve_allow_sus=_get_int("reserve_allow_sus", 0),
                reserve_allow_cov=_get_int("reserve_allow_cov", 0),
                reserve_allow_na=_get_int("reserve_allow_na", 0),
                reserve_allow_dnr=_get_int("reserve_allow_dnr", 0),
            )
        )

    overview.sort(
        key=lambda item: (
            sort_order.get(item.league_id, 9999),
            item.league_name.lower() if item.league_name else "",
        )
    )
    return overview


SETTINGS_FIELD_KEYS = [
    "bench_lock",
    "disable_adds",
    "offseason_adds",
    "disable_trades",
    "trade_deadline",
    "pick_trading",
    "trade_review_days",
    "veto_auto_poll",
    "veto_show_votes",
    "veto_votes_needed",
    "playoff_teams",
    "playoff_week_start",
    "league_average_match",
    "waiver_bid_min",
    "taxi_deadline",
    "taxi_allow_vets",
    "taxi_years",
    "reserve_allow_out",
    "reserve_allow_doubtful",
    "reserve_allow_sus",
    "reserve_allow_cov",
    "reserve_allow_na",
    "reserve_allow_dnr",
]


async def update_commissioner_settings(
    ctx: Context,
    payload: CommissionerSettingsUpdateRequest,
) -> CommissionerSettingsUpdateResponse:
    _require_commissioner_workspace_context(ctx)

    if not ctx.sleeper or not ctx.sleeper.can_write:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sleeper write access required. Please authenticate your Sleeper account.",
        )

    owned_rows = await get_visible_owned_league_rows_by_sleeper_user_id(
        db=ctx.db,
        sleeper_user_id=ctx.connection.sleeper_user_id or "",
        site_user_id=ctx.site_user.id,
        include_hidden=False,
    )
    owned_by_id = {
        row.league.league_id: row.league
        for row in owned_rows
        if row.league and getattr(row.roster, "is_owner", False) is True
    }

    # Extract non-None updates to apply
    updates_to_apply: dict[str, int] = {}
    for key in SETTINGS_FIELD_KEYS:
        val = getattr(payload, key, None)
        if val is not None:
            updates_to_apply[key] = int(val)

    results: list[CommissionerSettingsUpdateResult] = []
    successful_leagues = 0

    for league_id in payload.league_ids:
        league = owned_by_id.get(league_id)
        if not league:
            results.append(
                CommissionerSettingsUpdateResult(
                    league_id=league_id,
                    league_name="Unknown",
                    success=False,
                    error="Not an owned commissioner league",
                )
            )
            continue

        # Fetch live league settings to merge cleanly with all existing Sleeper keys
        live_league_settings: dict[str, Any] = {}
        if hasattr(ctx.sleeper, "read") and hasattr(ctx.sleeper.read, "transport"):
            try:
                raw_league = await ctx.sleeper.read.transport.get(f"league/{league.league_id}")
                if isinstance(raw_league, dict):
                    live_league_settings = raw_league.get("settings") or {}
            except Exception as ex:
                logger.warning("Could not fetch live raw league %s: %s", league.league_id, ex)

        merged_settings = {
            **(getattr(league, "settings", {}) or {}),
            **live_league_settings,
        }

        # Apply each updated setting
        for k, v in updates_to_apply.items():
            merged_settings[k] = v

        try:
            update_res = await ctx.sleeper.write.update_league_settings(
                league_id=league.league_id,
                settings_map=merged_settings,
            )

            updated_settings = update_res.get("settings") or merged_settings
            league.settings = updated_settings
            ctx.db.add(league)

            successful_leagues += 1
            results.append(
                CommissionerSettingsUpdateResult(
                    league_id=league.league_id,
                    league_name=league.name,
                    success=True,
                )
            )
        except Exception as ex:
            logger.error(
                "Failed to update settings for commissioner league %s: %s",
                league.league_id,
                ex,
                exc_info=True,
            )
            results.append(
                CommissionerSettingsUpdateResult(
                    league_id=league.league_id,
                    league_name=league.name,
                    success=False,
                    error=str(ex),
                )
            )

    if successful_leagues > 0:
        await ctx.db.commit()

    return CommissionerSettingsUpdateResponse(
        total_leagues=len(payload.league_ids),
        successful_leagues=successful_leagues,
        results=results,
    )
