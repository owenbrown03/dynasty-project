import asyncio
import logging
from typing import Any
from fastapi import HTTPException, status

from app.core.context import Context
from app.services.leagues.selection import (
    get_visible_owned_league_rows_by_sleeper_user_id,
)
from app.schemas.commissioner import (
    CommissionerStandardWaiverPreset,
    CommissionerStandardWaiverPresetUpdate,
    CommissionerWaiverDaySchedule,
    CommissionerWaiverLeagueInfo,
    CommissionerWaiverUpdateRequest,
    CommissionerWaiverUpdateResult,
    CommissionerWaiverUpdateResponse,
)

logger = logging.getLogger(__name__)


def to_base4_str(val: int | None) -> str:
    """Convert integer to 7-character base-4 string (Mon..Sun)."""
    if val is None:
        return "1111111"
    res = ""
    n = max(0, val)
    while n > 0:
        res = str(n % 4) + res
        n //= 4
    return res.zfill(7)


def decode_waiver_schedule(days_int: int | None) -> list[CommissionerWaiverDaySchedule]:
    """
    Decodes Sleeper's 7-digit base-4 string (Mon..Sun) into a 7-day schedule
    ordered from Sunday through Saturday.
    """
    b4 = to_base4_str(days_int)
    # b4 indices: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
    days_order = [
        ("Sunday", int(b4[6])),
        ("Monday", int(b4[0])),
        ("Tuesday", int(b4[1])),
        ("Wednesday", int(b4[2])),
        ("Thursday", int(b4[3])),
        ("Friday", int(b4[4])),
        ("Saturday", int(b4[5])),
    ]
    return [CommissionerWaiverDaySchedule(day=d, setting=v) for d, v in days_order]


def sun_sat_to_days_int(sun_to_sat: list[int]) -> int:
    """
    Converts a 7-element list [Sun, Mon, Tue, Wed, Thu, Fri, Sat] (values 0..3)
    into Sleeper's daily_waivers_days integer.
    """
    if len(sun_to_sat) != 7:
        raise ValueError("sun_to_sat must contain exactly 7 integers")
    # Sleeper internal day order: Mon, Tue, Wed, Thu, Fri, Sat, Sun
    mon_to_sun = [
        sun_to_sat[1],  # Mon
        sun_to_sat[2],  # Tue
        sun_to_sat[3],  # Wed
        sun_to_sat[4],  # Thu
        sun_to_sat[5],  # Fri
        sun_to_sat[6],  # Sat
        sun_to_sat[0],  # Sun
    ]
    base4_str = "".join(str(max(0, min(3, int(d)))) for d in mon_to_sun)
    return int(base4_str, 4)


def _require_commissioner_workspace_context(ctx: Context) -> None:
    if ctx.site_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    if ctx.connection is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sleeper connection required",
        )


def _extract_settings(league_obj: Any) -> dict[str, Any]:
    if not league_obj:
        return {}
    settings = getattr(league_obj, "settings", None)
    if isinstance(settings, dict):
        return settings
    if hasattr(settings, "model_dump"):
        return settings.model_dump(exclude_unset=True)
    if hasattr(settings, "dict"):
        return settings.dict(exclude_unset=True)
    if isinstance(league_obj, dict):
        return league_obj.get("settings") or {}
    return {}


async def get_commissioner_waivers_overview(
    ctx: Context,
) -> list[CommissionerWaiverLeagueInfo]:
    _require_commissioner_workspace_context(ctx)

    owned_rows = await get_visible_owned_league_rows_by_sleeper_user_id(
        db=ctx.db,
        sleeper_user_id=ctx.connection.sleeper_user_id or "",
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

    overview: list[CommissionerWaiverLeagueInfo] = []
    for row in commish_rows:
        league = row.league
        settings = getattr(league, "settings", {}) or {}
        daily_waivers = int(settings.get("daily_waivers", 0) or 0)
        daily_waivers_hour = int(settings.get("daily_waivers_hour", 0) or 0)
        daily_waivers_days = int(settings.get("daily_waivers_days", 5461) or 5461)
        waiver_type = int(settings.get("waiver_type", 2) or 2)
        val_clear = settings.get("waiver_clear_days")
        waiver_clear_days = int(val_clear) if val_clear is not None else 2
        val_day = settings.get("waiver_day_of_week")
        waiver_day_of_week = int(val_day) if val_day is not None else 2

        overview.append(
            CommissionerWaiverLeagueInfo(
                league_id=league.league_id,
                league_name=league.name,
                avatar=league.avatar,
                total_rosters=league.total_rosters,
                daily_waivers=daily_waivers,
                daily_waivers_hour=daily_waivers_hour,
                daily_waivers_days=daily_waivers_days,
                daily_waivers_days_b4=to_base4_str(daily_waivers_days),
                waiver_type=waiver_type,
                waiver_clear_days=waiver_clear_days,
                waiver_day_of_week=waiver_day_of_week,
                schedule=decode_waiver_schedule(daily_waivers_days),
            )
        )

    # Sort alphabetically by league name
    overview.sort(key=lambda item: item.league_name.lower())
    return overview


async def update_commissioner_waivers(
    ctx: Context,
    payload: CommissionerWaiverUpdateRequest,
) -> CommissionerWaiverUpdateResponse:
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

    # Determine target daily_waivers_days
    if payload.sunday_to_saturday_settings is not None and len(payload.sunday_to_saturday_settings) == 7:
        target_days = sun_sat_to_days_int(payload.sunday_to_saturday_settings)
    elif payload.daily_waivers_days is not None:
        target_days = payload.daily_waivers_days
    else:
        target_days = 5461

    results: list[CommissionerWaiverUpdateResult] = []
    successful_leagues = 0

    for league_id in payload.league_ids:
        league = owned_by_id.get(league_id)
        if not league:
            results.append(
                CommissionerWaiverUpdateResult(
                    league_id=league_id,
                    league_name="Unknown",
                    success=False,
                    error="Not an owned commissioner league",
                )
            )
            continue

        # Fetch live league settings to ensure we merge cleanly with all required Sleeper keys
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

        # Apply waiver modifications
        merged_settings["daily_waivers"] = int(payload.daily_waivers)
        merged_settings["daily_waivers_days"] = int(target_days)
        if payload.daily_waivers_hour is not None:
            merged_settings["daily_waivers_hour"] = int(payload.daily_waivers_hour)
        if payload.waiver_clear_days is not None:
            merged_settings["waiver_clear_days"] = int(payload.waiver_clear_days)
        if payload.waiver_day_of_week is not None:
            merged_settings["waiver_day_of_week"] = int(payload.waiver_day_of_week)

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
                CommissionerWaiverUpdateResult(
                    league_id=league.league_id,
                    league_name=league.name,
                    success=True,
                )
            )
        except Exception as ex:
            logger.error("Failed to update waivers on league %s (%s): %s", league.league_id, league.name, ex)
            results.append(
                CommissionerWaiverUpdateResult(
                    league_id=league.league_id,
                    league_name=league.name,
                    success=False,
                    error=str(ex),
                )
            )

    try:
        await ctx.db.commit()
    except Exception as ex:
        logger.error("Failed to commit updated league settings to local DB: %s", ex)

    return CommissionerWaiverUpdateResponse(
        total_leagues=len(payload.league_ids),
        successful_leagues=successful_leagues,
        results=results,
    )


DEFAULT_STANDARD_WAIVER_DAYS = [3, 0, 1, 1, 3, 3, 3]  # Sun, Mon, Tue, Wed, Thu, Fri, Sat
DEFAULT_OFFSEASON_WAIVER_DAYS = [2, 2, 2, 1, 2, 2, 2]  # Wed Waivers, other days Locked
DEFAULT_STANDARD_WAIVER_HOUR = None
DEFAULT_STANDARD_DAILY_WAIVERS = 1


def _get_preset_from_dict(
    raw: dict | None,
    default_days: list[int] = DEFAULT_STANDARD_WAIVER_DAYS,
) -> CommissionerStandardWaiverPreset:
    if not raw or not isinstance(raw, dict):
        return CommissionerStandardWaiverPreset(
            sunday_to_saturday_settings=default_days,
            daily_waivers_hour=DEFAULT_STANDARD_WAIVER_HOUR,
            daily_waivers=DEFAULT_STANDARD_DAILY_WAIVERS,
            is_custom=False,
        )
    days = raw.get("sunday_to_saturday_settings")
    if not isinstance(days, list) or len(days) != 7:
        days = default_days
    return CommissionerStandardWaiverPreset(
        sunday_to_saturday_settings=days,
        daily_waivers_hour=raw.get("daily_waivers_hour", DEFAULT_STANDARD_WAIVER_HOUR),
        daily_waivers=raw.get("daily_waivers", DEFAULT_STANDARD_DAILY_WAIVERS),
        is_custom=True,
    )


async def get_commissioner_standard_waiver_preset(
    ctx: Context,
    preset_type: str = "inseason",
) -> CommissionerStandardWaiverPreset:
    key = "commissioner_offseason_waivers" if preset_type == "offseason" else "commissioner_standard_waivers"
    default_days = DEFAULT_OFFSEASON_WAIVER_DAYS if preset_type == "offseason" else DEFAULT_STANDARD_WAIVER_DAYS

    if ctx.site_user and ctx.site_user.settings:
        custom = ctx.site_user.settings.get(key)
        if custom:
            return _get_preset_from_dict(custom, default_days=default_days)

    if ctx.session and ctx.session.settings:
        custom = ctx.session.settings.get(key)
        if custom:
            return _get_preset_from_dict(custom, default_days=default_days)

    return _get_preset_from_dict(None, default_days=default_days)


async def save_commissioner_standard_waiver_preset(
    ctx: Context,
    body: CommissionerStandardWaiverPresetUpdate,
    preset_type: str = "inseason",
) -> CommissionerStandardWaiverPreset:
    key = "commissioner_offseason_waivers" if preset_type == "offseason" else "commissioner_standard_waivers"
    preset_data = body.model_dump()

    if ctx.site_user:
        settings = dict(ctx.site_user.settings or {})
        settings[key] = preset_data
        ctx.site_user.settings = settings
        ctx.db.add(ctx.site_user)

    if ctx.session:
        settings = dict(ctx.session.settings or {})
        settings[key] = preset_data
        ctx.session.settings = settings
        ctx.db.add(ctx.session)

    await ctx.db.commit()
    if ctx.site_user:
        await ctx.db.refresh(ctx.site_user)
    if ctx.session:
        await ctx.db.refresh(ctx.session)

    return CommissionerStandardWaiverPreset(
        sunday_to_saturday_settings=body.sunday_to_saturday_settings,
        daily_waivers_hour=body.daily_waivers_hour if body.daily_waivers_hour is not None else DEFAULT_STANDARD_WAIVER_HOUR,
        daily_waivers=body.daily_waivers,
        is_custom=True,
    )


async def reset_commissioner_standard_waiver_preset(
    ctx: Context,
    preset_type: str = "inseason",
) -> CommissionerStandardWaiverPreset:
    key = "commissioner_offseason_waivers" if preset_type == "offseason" else "commissioner_standard_waivers"
    default_days = DEFAULT_OFFSEASON_WAIVER_DAYS if preset_type == "offseason" else DEFAULT_STANDARD_WAIVER_DAYS

    if ctx.site_user and ctx.site_user.settings and key in ctx.site_user.settings:
        settings = dict(ctx.site_user.settings)
        settings.pop(key, None)
        ctx.site_user.settings = settings
        ctx.db.add(ctx.site_user)

    if ctx.session and ctx.session.settings and key in ctx.session.settings:
        settings = dict(ctx.session.settings)
        settings.pop(key, None)
        ctx.session.settings = settings
        ctx.db.add(ctx.session)

    await ctx.db.commit()
    if ctx.site_user:
        await ctx.db.refresh(ctx.site_user)
    if ctx.session:
        await ctx.db.refresh(ctx.session)

    return _get_preset_from_dict(None, default_days=default_days)


