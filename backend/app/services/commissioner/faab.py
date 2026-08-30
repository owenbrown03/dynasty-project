from __future__ import annotations

import logging
from fastapi import HTTPException, status

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
        ctx.db,
        ctx.connection.sleeper_user_id,
    )
    if not owned_rows:
        return []

    overview: list[CommissionerFaabLeagueInfo] = []

    for row in owned_rows:
        league = row.league
        if not league:
            continue

        settings = getattr(league, "settings", {}) or {}
        default_budget = settings.get("waiver_budget", 100) or 100

        rosters = await get_all_rosters_by_league(
            ctx.db,
            league.league_id,
        )
        user_ids = [r.owner_id for r in rosters if r.owner_id]
        users = await get_users(ctx.db, user_ids)
        users_by_id = {u.user_id: u for u in users}

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
        ctx.db,
        ctx.connection.sleeper_user_id,
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

        settings = getattr(league, "settings", {}) or {}
        default_budget = settings.get("waiver_budget", 100) or 100
        target = (
            payload.target_budget
            if payload.target_budget is not None
            else default_budget
        )
        target_used = max(0, default_budget - target)

        rosters = await get_all_rosters_by_league(
            ctx.db,
            league.league_id,
        )
        rosters_reset = 0
        success = True
        error = None

        try:
            for roster in rosters:
                r_settings = getattr(roster, "settings", {}) or {}
                used = r_settings.get("waiver_budget_used", 0) or 0
                if default_budget - used != target:
                    if ctx.sleeper_write and ctx.sleeper_write.auth.is_authenticated():
                        await ctx.sleeper_write.reset_roster_faab(
                            league_id=league.league_id,
                            roster_id=roster.roster_id,
                            target_budget=target_used,
                        )
                    rosters_reset += 1

                    # Update local DB settings
                    roster.settings = {
                        **r_settings,
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
