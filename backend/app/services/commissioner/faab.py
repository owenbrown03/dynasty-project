import logging
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import Context
from app.models.db.sleeper.api import League as SleeperLeague
from app.models.db.sleeper.api import Roster as SleeperRoster
from app.schemas.commissioner import (
    CommissionerFaabRosterInfo,
    CommissionerFaabLeagueInfo,
    CommissionerFaabResetRequest,
    CommissionerFaabResetResult,
    CommissionerFaabResetResponse,
)

logger = logging.getLogger(__name__)

async def get_commissioner_faab_overview(ctx: Context) -> list[CommissionerFaabLeagueInfo]:
    stmt = (
        select(SleeperLeague)
        .where(
            SleeperLeague.is_commissioner == True,
            SleeperLeague.owner_id == ctx.user_id,
            SleeperLeague.status != "pre_draft"
        )
        .options(
            selectinload(SleeperLeague.rosters).selectinload(SleeperRoster.owner)
        )
    )
    result = await ctx.db.execute(stmt)
    leagues = result.scalars().unique().all()
    
    overview = []
    for league in leagues:
        default_budget = league.settings.get("waiver_budget", 100)
        
        rosters_info = []
        rosters_with_spent_faab = 0
        for roster in league.rosters:
            used = roster.settings.get("waiver_budget_used", 0)
            if used > 0:
                rosters_with_spent_faab += 1
            
            owner_name = roster.owner.display_name if roster.owner else None
            owner_avatar = roster.owner.avatar if roster.owner else None
            
            rosters_info.append(
                CommissionerFaabRosterInfo(
                    roster_id=roster.roster_id,
                    owner_name=owner_name,
                    owner_avatar=owner_avatar,
                    current_budget=default_budget - used,
                    budget_used=used
                )
            )
            
        overview.append(
            CommissionerFaabLeagueInfo(
                league_id=league.league_id,
                league_name=league.name,
                avatar=league.avatar,
                default_budget=default_budget,
                total_rosters=len(league.rosters),
                rosters_with_spent_faab=rosters_with_spent_faab,
                rosters=rosters_info
            )
        )
        
    return overview


async def reset_commissioner_faab(ctx: Context, payload: CommissionerFaabResetRequest) -> CommissionerFaabResetResponse:
    if not ctx.sleeper:
        raise ValueError("Sleeper not connected")
        
    results = []
    total_leagues = len(payload.league_ids)
    successful_leagues = 0
    
    stmt = (
        select(SleeperLeague)
        .where(
            SleeperLeague.league_id.in_(payload.league_ids),
            SleeperLeague.is_commissioner == True,
            SleeperLeague.owner_id == ctx.user_id
        )
        .options(
            selectinload(SleeperLeague.rosters)
        )
    )
    result = await ctx.db.execute(stmt)
    leagues_dict = {l.league_id: l for l in result.scalars().unique().all()}
    
    for league_id in payload.league_ids:
        league = leagues_dict.get(league_id)
        if not league:
            results.append(CommissionerFaabResetResult(
                league_id=league_id,
                league_name="Unknown",
                rosters_reset=0,
                success=False,
                error="Not found or not commissioner"
            ))
            continue
            
        default_budget = league.settings.get("waiver_budget", 100)
        target = payload.target_budget if payload.target_budget is not None else default_budget
        # budget_used should be (default_budget - target_budget)
        target_used = default_budget - target
        
        rosters_reset = 0
        success = True
        error = None
        
        try:
            for roster in league.rosters:
                used = roster.settings.get("waiver_budget_used", 0)
                if default_budget - used != target:
                    await ctx.sleeper.write.reset_roster_faab(
                        league_id=league.league_id,
                        roster_id=roster.roster_id,
                        target_budget=target_used
                    )
                    rosters_reset += 1
                    
                    # Update DB
                    roster.settings = {**roster.settings, "waiver_budget_used": target_used}
                    ctx.db.add(roster)
            
            await ctx.db.commit()
            successful_leagues += 1
        except Exception as e:
            logger.exception(f"Error resetting faab for league {league_id}")
            success = False
            error = str(e)
            
        results.append(CommissionerFaabResetResult(
            league_id=league.league_id,
            league_name=league.name,
            rosters_reset=rosters_reset,
            success=success,
            error=error
        ))
        
    return CommissionerFaabResetResponse(
        total_leagues=total_leagues,
        successful_leagues=successful_leagues,
        results=results
    )
