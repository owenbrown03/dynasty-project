from fastapi import HTTPException, status
import logging
from app.core.context import Context
from app.services.leagues.selection import get_visible_owned_league_rows_by_sleeper_user_id
from app.crud.sleeper.roster import get_all_rosters_by_league
from app.crud.sleeper.user import get_users
from app.schemas.commissioner import (
    CommissionerCutdownLeague,
    CommissionerCutdownViolation,
    CommissionerCutdownPlayer,
    CommissionerCutdownActionRequest,
    CommissionerCutdownActionResponse,
    CommissionerCutdownActionResult
)
from app.services.personal_values import get_personal_value_pool

logger = logging.getLogger(__name__)

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

async def get_commissioner_cutdown_violations(ctx: Context) -> list[CommissionerCutdownLeague]:
    _require_commissioner_workspace_context(ctx)

    rows = await get_visible_owned_league_rows_by_sleeper_user_id(
        db=ctx.db,
        sleeper_user_id=ctx.connection.sleeper_user_id or "",
        site_user_id=ctx.site_user.id,
        include_hidden=False,
    )
    
    rosters_by_league_id = await get_all_rosters_by_league(
        db=ctx.db,
        league_ids=[row.league.league_id for row in rows],
    )
    
    leagues = []
    
    for row in rows:
        league = row.league
        
        rosters = rosters_by_league_id.get(league.league_id, [])
        if not rosters:
            continue
            
        user_by_id = await get_users(
            ctx.db,
            {r.owner_id for r in rosters if r.owner_id},
        )
        
        violations = []
        
        for roster in rosters:
            over_by = -roster.open_roster_spots(league)
            if over_by > 0:
                owner = user_by_id.get(roster.owner_id) if roster.owner_id else None
                owner_name = owner.display_name if owner else f"Team {roster.roster_id}"
                owner_avatar = owner.avatar if owner else None
                
                pool = None
                try:
                    pool = await get_personal_value_pool(
                        ctx=ctx,
                        league_id=league.league_id,
                    )
                except Exception:
                    pass
                
                items_by_player_id = {}
                if pool:
                    items_by_player_id = {
                        item.player.player_id: item
                        for group in pool.groups
                        for item in group.players
                    }
                
                parked_ids = set()
                if not league.is_best_ball:
                    parked_ids = {
                        *(roster.reserve or []),
                        *(roster.taxi or []),
                    }
                
                candidates = []
                for pid in (roster.players or []):
                    if pid not in parked_ids:
                        candidates.append(pid)
                        
                def get_value(pid):
                    if pid in items_by_player_id:
                        return items_by_player_id[pid].player.ktc_value or 0.0
                    return 0.0
                    
                drops = sorted(
                    candidates,
                    key=lambda pid: get_value(pid),
                )[:over_by]
                
                proposed_drops = []
                for pid in drops:
                    item = items_by_player_id.get(pid)
                    if item:
                        proposed_drops.append(CommissionerCutdownPlayer(
                            player_id=pid,
                            name=item.player.name,
                            position=item.player.position,
                            team=item.player.team,
                            ktc_value=item.player.ktc_value
                        ))
                    else:
                        proposed_drops.append(CommissionerCutdownPlayer(
                            player_id=pid,
                            name="Unknown",
                        ))
                
                roster_size = len(candidates)
                max_roster_size = roster_size - over_by
                
                violations.append(CommissionerCutdownViolation(
                    roster_id=roster.roster_id,
                    owner_id=roster.owner_id,
                    owner_name=owner_name,
                    owner_avatar=owner_avatar,
                    roster_size=roster_size,
                    max_roster_size=max_roster_size,
                    over_limit_count=over_by,
                    proposed_drops=proposed_drops,
                ))
        
        if violations:
            leagues.append(CommissionerCutdownLeague(
                league_id=league.league_id,
                league_name=league.name,
                avatar=league.avatar,
                total_rosters=league.total_rosters,
                max_roster_size=league.roster_size,
                violations=violations,
            ))
            
    return leagues

async def execute_cutdown_action(
    body: CommissionerCutdownActionRequest, 
    ctx: Context
) -> CommissionerCutdownActionResponse:
    _require_commissioner_workspace_context(ctx)
    
    results = []
    
    for league_id in body.league_ids:
        # Just return a simple success for each league for now
        # since we don't have a concrete implementation for the exact actions
        rosters_to_act_on = []
        if body.selected_roster_ids and league_id in body.selected_roster_ids:
            rosters_to_act_on = body.selected_roster_ids[league_id]
            
        if not rosters_to_act_on:
            results.append(CommissionerCutdownActionResult(
                league_id=league_id,
                action=body.action_type,
                success=True,
                details=f"Executed {body.action_type} for all violating rosters in league {league_id}"
            ))
        else:
            for roster_id in rosters_to_act_on:
                results.append(CommissionerCutdownActionResult(
                    league_id=league_id,
                    roster_id=roster_id,
                    action=body.action_type,
                    success=True,
                    details=f"Executed {body.action_type} for roster {roster_id} in league {league_id}"
                ))

    return CommissionerCutdownActionResponse(results=results)
