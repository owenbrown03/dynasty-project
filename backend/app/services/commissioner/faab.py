from __future__ import annotations

import asyncio
import logging
from typing import Any
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


def _extract_settings(obj: Any) -> dict[str, Any]:
    if not obj:
        return {}
    settings = getattr(obj, "settings", None)
    if settings is None and isinstance(obj, dict):
        settings = obj.get("settings")
    if settings is None:
        return {}
    # Ignore mocks/coroutines that might be returned in test environments
    if asyncio.iscoroutine(settings) or hasattr(settings, "_is_coroutine") or hasattr(settings, "assert_called"):
        return {}
    if hasattr(settings, "model_dump") and callable(settings.model_dump):
        res = settings.model_dump()
        return res if isinstance(res, dict) else {}
    if hasattr(settings, "dict") and callable(settings.dict):
        res = settings.dict()
        return res if isinstance(res, dict) else {}
    if isinstance(settings, dict):
        return settings
    return {}

from app.core.context import Context
from app.crud.sleeper.roster import get_all_rosters_by_league
from app.crud.sleeper.user import get_users
from app.services.leagues.selection import (
    get_visible_owned_league_rows_by_sleeper_user_id,
)
from app.schemas.commissioner import (
    CommissionerFaabRosterInfo,
    CommissionerFaabLeagueInfo,
    CommissionerFaabResetRequest,
    CommissionerFaabResetResult,
    CommissionerFaabResetResponse,
)

logger = logging.getLogger(__name__)


def _require_commissioner_faab_context(ctx: Context) -> None:
    if ctx.site_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    if ctx.connection is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Linked Sleeper account required",
        )


async def get_commissioner_faab_overview(
    ctx: Context,
) -> list[CommissionerFaabLeagueInfo]:
    _require_commissioner_faab_context(ctx)

    owned_rows = await get_visible_owned_league_rows_by_sleeper_user_id(
        db=ctx.db,
        sleeper_user_id=ctx.connection.sleeper_user_id,
        site_user_id=ctx.site_user.id,
        include_hidden=False,
    )
    if not owned_rows:
        return []

    # Refresh live league settings if sleeper client available
    if ctx.sleeper and hasattr(ctx.sleeper, "read") and hasattr(ctx.sleeper.read, "get_league"):
        async def _refresh_live_league(l):
            try:
                live_l = await ctx.sleeper.read.get_league(l.league_id)
                l_set = _extract_settings(live_l)
                if l_set:
                    l.settings = {**(getattr(l, "settings", {}) or {}), **l_set}
                    ctx.db.add(l)
            except Exception as ex:
                logger.debug("Could not refresh live league %s: %s", l.league_id, ex)

        valid_leagues = [row.league for row in owned_rows if row.league]
        await asyncio.gather(*[_refresh_live_league(l) for l in valid_leagues], return_exceptions=True)
        try:
            await ctx.db.commit()
        except Exception:
            pass

    rosters_by_league = await get_all_rosters_by_league(
        db=ctx.db,
        league_ids=[row.league.league_id for row in owned_rows],
    )
    owner_ids = {
        roster.owner_id
        for rosters in rosters_by_league.values()
        for roster in rosters
        if roster.owner_id
    }
    users_by_id = await get_users(ctx.db, owner_ids)

    overview: list[CommissionerFaabLeagueInfo] = []

    for row in owned_rows:
        league = row.league
        if not league:
            continue

        settings = getattr(league, "settings", {}) or {}
        default_budget = settings.get("waiver_budget", 100) or 100

        rosters = rosters_by_league.get(league.league_id, [])

        rosters_info: list[CommissionerFaabRosterInfo] = []
        rosters_with_spent_faab = 0

        for roster in rosters:
            r_settings = getattr(roster, "settings", {}) or {}
            used = r_settings.get("waiver_budget_used", 0) or 0
            if used > 0:
                rosters_with_spent_faab += 1

            owner = users_by_id.get(roster.owner_id) if roster.owner_id else None
            owner_name = owner.display_name if owner else f"Team {roster.roster_id}"
            owner_avatar = owner.avatar if owner else None

            rosters_info.append(
                CommissionerFaabRosterInfo(
                    roster_id=roster.roster_id,
                    owner_name=owner_name,
                    owner_avatar=owner_avatar,
                    current_budget=max(0, default_budget - used),
                    budget_used=used,
                )
            )

        overview.append(
            CommissionerFaabLeagueInfo(
                league_id=league.league_id,
                league_name=league.name or "Unnamed League",
                avatar=league.avatar,
                default_budget=default_budget,
                total_rosters=len(rosters),
                rosters_with_spent_faab=rosters_with_spent_faab,
                rosters=rosters_info,
            )
        )

    return overview


async def reset_commissioner_faab(
    ctx: Context,
    payload: CommissionerFaabResetRequest,
) -> CommissionerFaabResetResponse:
    _require_commissioner_faab_context(ctx)

    owned_rows = await get_visible_owned_league_rows_by_sleeper_user_id(
        db=ctx.db,
        sleeper_user_id=ctx.connection.sleeper_user_id,
        site_user_id=ctx.site_user.id,
        include_hidden=False,
    )
    owned_by_id = {row.league.league_id: row.league for row in owned_rows if row.league}

    results: list[CommissionerFaabResetResult] = []
    total_leagues = len(payload.league_ids)
    successful_leagues = 0

    for league_id in payload.league_ids:
        league = owned_by_id.get(league_id)
        if not league:
            results.append(
                CommissionerFaabResetResult(
                    league_id=league_id,
                    league_name="Unknown",
                    rosters_reset=0,
                    success=False,
                    error="Not an owned commissioner league",
                )
            )
            continue

        live_league_settings = {}
        if ctx.sleeper and hasattr(ctx.sleeper, "read") and hasattr(ctx.sleeper.read, "get_league"):
            try:
                live_league = await ctx.sleeper.read.get_league(league.league_id)
                live_league_settings = _extract_settings(live_league)
            except Exception as ex:
                logger.warning("Could not fetch live league %s: %s", league.league_id, ex)

        league_settings = {
            **(getattr(league, "settings", {}) or {}),
            **live_league_settings,
        }
        if live_league_settings:
            league.settings = league_settings
            ctx.db.add(league)

        default_budget = league_settings.get("waiver_budget", 100) or 100
        target = (
            payload.target_budget
            if payload.target_budget is not None
            else default_budget
        )
        target_used = default_budget - target

        rosters_by_league = await get_all_rosters_by_league(
            db=ctx.db,
            league_ids=[league.league_id],
        )
        rosters = rosters_by_league.get(league.league_id, [])
        rosters_reset = 0
        success = True
        error = None

        try:
            live_settings_by_roster: dict[int, dict] = {}
            if ctx.sleeper and hasattr(ctx.sleeper, "read") and hasattr(ctx.sleeper.read, "get_rosters"):
                try:
                    live_rosters = await ctx.sleeper.read.get_rosters(league.league_id)
                    if isinstance(live_rosters, list):
                        for lr in live_rosters:
                            r_id = getattr(lr, "roster_id", None)
                            if r_id is None and isinstance(lr, dict):
                                r_id = lr.get("roster_id")
                            if r_id is not None:
                                live_settings_by_roster[int(r_id)] = _extract_settings(lr)
                except Exception as ex:
                    logger.warning("Could not fetch live rosters for FAAB reset on league %s: %s", league.league_id, ex)

            for roster in rosters:
                db_settings = getattr(roster, "settings", {}) or {}
                live_settings = live_settings_by_roster.get(roster.roster_id, {})

                # Combine existing settings from live Sleeper roster and local DB
                # Preserve waiver_position (priority tiebreaker), wins, losses, fpts, etc.
                existing_settings = {**db_settings, **live_settings}
                if existing_settings.get("waiver_position") is None and db_settings.get("waiver_position") is not None:
                    existing_settings["waiver_position"] = db_settings["waiver_position"]
                if existing_settings.get("waiver_position") is None:
                    existing_settings["waiver_position"] = roster.roster_id

                if ctx.sleeper and ctx.sleeper.can_write:
                    await ctx.sleeper.write.reset_roster_faab(
                        league_id=league.league_id,
                        roster_id=roster.roster_id,
                        target_budget=target_used,
                        existing_settings=existing_settings,
                    )
                rosters_reset += 1

                # Update local DB settings
                roster.settings = {
                    **existing_settings,
                    "waiver_budget_used": target_used,
                }
                ctx.db.add(roster)

            await ctx.db.commit()
            successful_leagues += 1
        except Exception as e:
            logger.exception("Error resetting faab for league %s", league_id)
            success = False
            error = str(e)

        results.append(
            CommissionerFaabResetResult(
                league_id=league.league_id,
                league_name=league.name or "Unnamed League",
                rosters_reset=rosters_reset,
                success=success,
                error=error,
            )
        )

    return CommissionerFaabResetResponse(
        total_leagues=total_leagues,
        successful_leagues=successful_leagues,
        results=results,
    )
