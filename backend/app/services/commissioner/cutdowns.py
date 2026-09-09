from fastapi import HTTPException, status
import logging
from sqlmodel import select
from app.core.context import Context
from app.services.leagues.selection import get_visible_owned_league_rows_by_sleeper_user_id
from app.crud.sleeper.roster import get_all_rosters_by_league
from app.crud.sleeper.user import get_users
from app.models.db.ktc.models import KTCValue
from app.models.db.sleeper.api import Player
from app.schemas.commissioner import (
    CommissionerCutdownLeague,
    CommissionerCutdownViolation,
    CommissionerCutdownPlayer,
    CommissionerCutdownActionRequest,
    CommissionerCutdownActionResponse,
    CommissionerCutdownActionResult
)

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

async def _compute_league_violations(
    ctx: Context,
    league,
    rosters,
) -> list[CommissionerCutdownViolation]:
    if not rosters:
        return []

    over_rosters = []
    for roster in rosters:
        over_by = -roster.open_roster_spots(league)
        if over_by > 0:
            over_rosters.append((roster, over_by))

    if not over_rosters:
        return []

    user_by_id = await get_users(
        ctx.db,
        {r.owner_id for r, _ in over_rosters if r.owner_id},
    )

    over_player_ids = {
        pid
        for roster, _ in over_rosters
        for pid in (roster.players or [])
    }
    items_by_player_id = {}
    if over_player_ids:
        player_rows = (
            await ctx.db.execute(
                select(Player).where(
                    Player.player_id.in_(over_player_ids)
                )
            )
        ).scalars().all()
        ktc_rows = (
            await ctx.db.execute(
                select(KTCValue).where(
                    KTCValue.player_id.in_(over_player_ids)
                )
            )
        ).scalars().all()
        ktc_by_player_id = {
            row.player_id: (row.sf_value if row.sf_value is not None else row.value)
            for row in ktc_rows
        }
        items_by_player_id = {
            player.player_id: {
                "name": player.full_name,
                "position": player.position,
                "team": player.team,
                "ktc_value": ktc_by_player_id.get(player.player_id),
            }
            for player in player_rows
        }

    parkable = not league.is_best_ball
    violations = []

    for roster, over_by in over_rosters:
        owner = user_by_id.get(roster.owner_id) if roster.owner_id else None
        owner_name = (owner.display_name or owner.username) if owner else f"Team {roster.roster_id}"
        owner_avatar = owner.avatar if owner else None

        parked_ids = set()
        if parkable:
            parked_ids = {
                *(roster.reserve or []),
                *(roster.taxi or []),
            }

        candidates = []
        for pid in (roster.players or []):
            if pid not in parked_ids:
                candidates.append(pid)

        def get_value(pid):
            item = items_by_player_id.get(pid)
            if item is not None and item["ktc_value"] is not None:
                return item["ktc_value"]
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
                    name=item["name"],
                    position=item["position"],
                    team=item["team"],
                    ktc_value=item["ktc_value"],
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

    return violations


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
        violations = await _compute_league_violations(ctx, league, rosters)

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
    ctx: Context,
) -> CommissionerCutdownActionResponse:
    _require_commissioner_workspace_context(ctx)

    if not ctx.sleeper or not ctx.sleeper.can_write:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sleeper write access required",
        )

    owned_rows = await get_visible_owned_league_rows_by_sleeper_user_id(
        db=ctx.db,
        sleeper_user_id=ctx.connection.sleeper_user_id or "",
        site_user_id=ctx.site_user.id,
        include_hidden=False,
    )
    owned_league_dict = {row.league.league_id: row.league for row in owned_rows}

    rosters_by_league = await get_all_rosters_by_league(
        db=ctx.db,
        league_ids=body.league_ids,
    )

    results = []

    for league_id in body.league_ids:
        league = owned_league_dict.get(league_id)
        if not league:
            results.append(
                CommissionerCutdownActionResult(
                    league_id=league_id,
                    action=body.action_type,
                    success=False,
                    error="Not an owned league or league not found.",
                )
            )
            continue

        rosters = rosters_by_league.get(league_id, [])
        try:
            violations = await _compute_league_violations(ctx, league, rosters)
        except Exception as exc:
            logger.exception("Failed to compute cutdown violations for league %s: %s", league_id, exc)
            results.append(
                CommissionerCutdownActionResult(
                    league_id=league_id,
                    action=body.action_type,
                    success=False,
                    error=f"Failed to calculate violations: {exc}",
                )
            )
            continue

        selected_rosters = None
        if body.selected_roster_ids and league_id in body.selected_roster_ids:
            selected_rosters = set(body.selected_roster_ids[league_id])

        if selected_rosters is not None:
            active_violations = [v for v in violations if v.roster_id in selected_rosters]
        else:
            active_violations = violations

        action = body.action_type
        if action in ("chat_all", "notify"):
            try:
                msg_text = (
                    body.custom_message
                    or "@all Friendly reminder from the commissioner: Please check your rosters and cut down to the league roster limit before the deadline."
                )
                await ctx.sleeper.write.create_message(
                    parent_type="league",
                    parent_id=league_id,
                    text=msg_text,
                )
                results.append(
                    CommissionerCutdownActionResult(
                        league_id=league_id,
                        action=action,
                        success=True,
                        details="Sent @all reminder to league chat",
                    )
                )
            except Exception as exc:
                logger.exception("Failed to send chat_all for league %s: %s", league_id, exc)
                results.append(
                    CommissionerCutdownActionResult(
                        league_id=league_id,
                        action=action,
                        success=False,
                        error=str(exc),
                    )
                )

        elif action == "chat_tag":
            if not active_violations:
                results.append(
                    CommissionerCutdownActionResult(
                        league_id=league_id,
                        action=action,
                        success=True,
                        details="No violating rosters to tag in league chat",
                    )
                )
                continue

            try:
                violating_names = [v.owner_name for v in active_violations if v.owner_name]
                prefix = body.custom_message or "Roster Cutdown Reminder:"
                tagged_str = ", ".join([f"@{name}" for name in violating_names])
                text = f"{prefix} The following managers are currently over the roster limit: {tagged_str}. Please cut down your rosters!"
                await ctx.sleeper.write.create_message(
                    parent_type="league",
                    parent_id=league_id,
                    text=text,
                )
                results.append(
                    CommissionerCutdownActionResult(
                        league_id=league_id,
                        action=action,
                        success=True,
                        details=f"Tagged {len(violating_names)} violating manager(s) in league chat",
                    )
                )
            except Exception as exc:
                logger.exception("Failed to send chat_tag for league %s: %s", league_id, exc)
                results.append(
                    CommissionerCutdownActionResult(
                        league_id=league_id,
                        action=action,
                        success=False,
                        error=str(exc),
                    )
                )

        elif action == "dm_warning":
            if not active_violations:
                results.append(
                    CommissionerCutdownActionResult(
                        league_id=league_id,
                        action=action,
                        success=True,
                        details="No violating rosters to DM",
                    )
                )
                continue

            for violation in active_violations:
                if not violation.owner_id:
                    results.append(
                        CommissionerCutdownActionResult(
                            league_id=league_id,
                            roster_id=violation.roster_id,
                            action=action,
                            success=False,
                            error="Roster has no owner ID",
                        )
                    )
                    continue

                try:
                    owner_name = violation.owner_name or f"Team {violation.roster_id}"
                    over_by = violation.over_limit_count
                    default_dm = f"Hi @{owner_name}, reminder that your roster in {league.name} is over the limit by {over_by} player(s). Please make your cuts."
                    dm_text = body.custom_message or default_dm
                    await ctx.sleeper.write.create_dm(
                        members=[violation.owner_id],
                        message_text=dm_text,
                    )
                    results.append(
                        CommissionerCutdownActionResult(
                            league_id=league_id,
                            roster_id=violation.roster_id,
                            action=action,
                            success=True,
                            details=f"Sent DM warning to @{owner_name}",
                        )
                    )
                except Exception as exc:
                    logger.exception(
                        "Failed to send DM warning to owner %s in league %s: %s",
                        violation.owner_id,
                        league_id,
                        exc,
                    )
                    results.append(
                        CommissionerCutdownActionResult(
                            league_id=league_id,
                            roster_id=violation.roster_id,
                            action=action,
                            success=False,
                            error=str(exc),
                        )
                    )

        elif action == "force_drop":
            if not active_violations:
                results.append(
                    CommissionerCutdownActionResult(
                        league_id=league_id,
                        action=action,
                        success=True,
                        details="No violating rosters to force drop",
                    )
                )
                continue

            # Fetch fresh live rosters from Sleeper so we always drop players
            # that are ACTUALLY currently on the roster in Sleeper!
            live_roster_by_id = {}
            if hasattr(ctx.sleeper, "read") and hasattr(ctx.sleeper.read, "get_rosters"):
                try:
                    live_rosters_data = await ctx.sleeper.read.get_rosters(league_id)
                    if isinstance(live_rosters_data, list):
                        live_roster_by_id = {
                            getattr(r, "roster_id", None) or (r.get("roster_id") if isinstance(r, dict) else None): r
                            for r in live_rosters_data
                            if hasattr(r, "roster_id") or (isinstance(r, dict) and "roster_id" in r)
                        }
                except Exception as exc:
                    logger.warning("Could not fetch live rosters from Sleeper for league %s: %s", league_id, exc)

            parkable = not league.is_best_ball
            max_roster_size = league.roster_size

            for violation in active_violations:
                live_roster = live_roster_by_id.get(violation.roster_id)
                db_roster = next((r for r in rosters if r.roster_id == violation.roster_id), None)

                # If live roster is available from Sleeper, verify actual live ownership and count
                if live_roster:
                    live_players_raw = getattr(live_roster, "players", None) or (live_roster.get("players") if isinstance(live_roster, dict) else None) or []
                    live_reserve_raw = getattr(live_roster, "reserve", None) or (live_roster.get("reserve") if isinstance(live_roster, dict) else None) or []
                    live_taxi_raw = getattr(live_roster, "taxi", None) or (live_roster.get("taxi") if isinstance(live_roster, dict) else None) or []

                    live_players = list(live_players_raw)
                    live_reserve = list(live_reserve_raw)
                    live_taxi = list(live_taxi_raw)

                    # Keep local DB roster updated with current reality
                    if db_roster:
                        db_roster.players = live_players
                        db_roster.reserve = live_reserve
                        db_roster.taxi = live_taxi
                        ctx.db.add(db_roster)

                    parked_ids = set()
                    if parkable:
                        parked_ids = set(live_reserve + live_taxi)
                    live_candidates = [pid for pid in live_players if pid not in parked_ids]
                    live_over_by = len(live_candidates) - max_roster_size

                    if live_over_by <= 0:
                        results.append(
                            CommissionerCutdownActionResult(
                                league_id=league_id,
                                roster_id=violation.roster_id,
                                action=action,
                                success=True,
                                details=f"Roster {violation.roster_id} is already compliant on Sleeper ({len(live_candidates)}/{max_roster_size} active players). No cuts needed.",
                            )
                        )
                        continue

                    # Query KTC values for live candidates to drop the lowest KTC players among live candidates
                    ktc_rows = (
                        await ctx.db.execute(
                            select(KTCValue).where(KTCValue.player_id.in_(live_candidates))
                        )
                    ).scalars().all()
                    ktc_by_id = {row.player_id: (row.sf_value if row.sf_value is not None else row.value) for row in ktc_rows}

                    def get_ktc_val(pid):
                        val = ktc_by_id.get(pid)
                        return val if val is not None else 0.0

                    player_ids_to_drop = sorted(live_candidates, key=get_ktc_val)[:live_over_by]
                else:
                    player_ids_to_drop = [drop.player_id for drop in violation.proposed_drops]

                if not player_ids_to_drop:
                    results.append(
                        CommissionerCutdownActionResult(
                            league_id=league_id,
                            roster_id=violation.roster_id,
                            action=action,
                            success=True,
                            details=f"No candidates to drop for roster {violation.roster_id}",
                        )
                    )
                    continue

                try:
                    await ctx.sleeper.write.league_mutation(
                        "league_create_transaction",
                        league_id,
                        {
                            "type": "commissioner",
                            "k_adds": [],
                            "v_adds": [],
                            "k_drops": player_ids_to_drop,
                            "v_drops": [violation.roster_id for _ in player_ids_to_drop],
                        },
                    )
                    if db_roster and db_roster.players:
                        drop_set = set(player_ids_to_drop)
                        db_roster.players = [p for p in db_roster.players if p not in drop_set]
                        ctx.db.add(db_roster)

                    results.append(
                        CommissionerCutdownActionResult(
                            league_id=league_id,
                            roster_id=violation.roster_id,
                            action=action,
                            success=True,
                            details=f"Dropped {len(player_ids_to_drop)} player(s) for roster {violation.roster_id}",
                        )
                    )
                except Exception as exc:
                    logger.exception(
                        "Failed to force drop players for roster %s in league %s: %s",
                        violation.roster_id,
                        league_id,
                        exc,
                    )
                    results.append(
                        CommissionerCutdownActionResult(
                            league_id=league_id,
                            roster_id=violation.roster_id,
                            action=action,
                            success=False,
                            error=str(exc),
                        )
                    )
        else:
            results.append(
                CommissionerCutdownActionResult(
                    league_id=league_id,
                    action=action,
                    success=False,
                    error=f"Unknown action type: {action}",
                )
            )

    await ctx.db.commit()
    return CommissionerCutdownActionResponse(results=results)

