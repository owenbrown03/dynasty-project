from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Iterable

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.core.concurrency import bounded_gather
from app.crud.value import get_player_values
from app.models.db.sleeper.api import (
    League,
    LeagueWeeklyRosterMetric,
    Player,
    Roster,
)
from app.services.leagues.details import (
    calculate_projected_starter_points,
    is_slot_eligible,
)
from app.services.leagues.models import LeaguePlayer

logger = logging.getLogger(__name__)

SLOT_RESTRICTION_ORDER = {
    "QB": 1,
    "K": 1,
    "DEF": 1,
    "DL": 1,
    "LB": 1,
    "DB": 1,
    "TE": 2,
    "RB": 3,
    "WR": 3,
    "WRRB_FLEX": 4,
    "REC_FLEX": 4,
    "FLEX": 5,
    "IDP_FLEX": 5,
    "SUPER_FLEX": 6,
    "OP": 6,
}


def _slot_sort_key(slot: str) -> int:
    return SLOT_RESTRICTION_ORDER.get(slot, 10)


def calculate_optimal_lineup_points(
    *,
    roster_positions: list[str],
    players_points: dict[str, float],
    player_positions: dict[str, str],
    actual_starter_points: float = 0.0,
) -> float:
    starter_slots = [
        slot
        for slot in roster_positions
        if slot not in {"BN", "IR", "TAXI"}
    ]
    if not starter_slots:
        return round(actual_starter_points, 2)

    # Sort starter slots from most restrictive (QB, TE, RB, WR) to flex
    sorted_slots = sorted(starter_slots, key=_slot_sort_key)

    available_players = [
        {
            "player_id": player_id,
            "points": float(pts or 0.0),
            "position": player_positions.get(player_id),
        }
        for player_id, pts in players_points.items()
    ]
    available_players.sort(key=lambda p: p["points"], reverse=True)

    assigned_player_ids: set[str] = set()
    total_optimal = 0.0

    for slot in sorted_slots:
        for player in available_players:
            if player["player_id"] in assigned_player_ids:
                continue
            if is_slot_eligible(slot, player["position"]):
                assigned_player_ids.add(player["player_id"])
                total_optimal += player["points"]
                break

    return round(max(total_optimal, actual_starter_points), 2)


async def get_league_weekly_metrics(
    db: AsyncSession,
    league_ids: Iterable[str],
    season: str | None = None,
    week: int | None = None,
    max_week: int | None = None,
) -> list[LeagueWeeklyRosterMetric]:
    league_ids = list(league_ids)
    if not league_ids:
        return []

    stmt = select(LeagueWeeklyRosterMetric).where(
        col(LeagueWeeklyRosterMetric.league_id).in_(league_ids)
    )
    if season is not None:
        stmt = stmt.where(LeagueWeeklyRosterMetric.season == season)
    if week is not None:
        stmt = stmt.where(LeagueWeeklyRosterMetric.week == week)
    if max_week is not None:
        stmt = stmt.where(LeagueWeeklyRosterMetric.week <= max_week)

    stmt = stmt.order_by(
        LeagueWeeklyRosterMetric.league_id,
        LeagueWeeklyRosterMetric.week,
        LeagueWeeklyRosterMetric.roster_id,
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def upsert_league_weekly_metrics(
    db: AsyncSession,
    rows: list[dict[str, Any]],
    batch_size: int = 500,
) -> None:
    if not rows:
        return

    now = datetime.utcnow()
    for row in rows:
        row.setdefault("created_at", now)
        row.setdefault("updated_at", now)

    for i in range(0, len(rows), batch_size):
        chunk = rows[i : i + batch_size]
        stmt = insert(LeagueWeeklyRosterMetric).values(chunk)
        update_dict = {
            "points": stmt.excluded.points,
            "max_points": stmt.excluded.max_points,
            "wins": stmt.excluded.wins,
            "losses": stmt.excluded.losses,
            "ties": stmt.excluded.ties,
            "starter_war": stmt.excluded.starter_war,
            "roster_war": stmt.excluded.roster_war,
            "sleeper_projection": stmt.excluded.sleeper_projection,
            "ktc_redraft": stmt.excluded.ktc_redraft,
            "fantasycalc_redraft": stmt.excluded.fantasycalc_redraft,
            "updated_at": now,
        }
        upsert_stmt = stmt.on_conflict_do_update(
            constraint="uq_league_weekly_roster_metric",
            set_=update_dict,
        )
        await db.execute(upsert_stmt)
    await db.commit()


async def sync_league_weekly_matchups(
    db: AsyncSession,
    sleeper: Any,
    leagues: list[League],
    current_week: int,
    redis: Any | None = None,
    war_by_league_id: dict[str, Any] | None = None,
    force_refresh: bool = False,
) -> int:
    if not leagues or current_week < 1 or sleeper is None:
        return 0

    league_ids = [league.league_id for league in leagues]
    existing = await get_league_weekly_metrics(
        db,
        league_ids=league_ids,
        max_week=current_week,
    )
    existing_keys = set()
    if not force_refresh:
        existing_keys = {
            (m.league_id, m.week)
            for m in existing
            if m.starter_war is not None and m.starter_war > 0
        }

    # Identify which (league, week) pairs are missing
    fetch_tasks = []
    for league in leagues:
        for week in range(1, current_week + 1):
            if (league.league_id, week) not in existing_keys:
                fetch_tasks.append((league, week))

    if not fetch_tasks:
        return 0

    # Calculate shared redraft WAR across leagues if not provided
    if war_by_league_id is None:
        try:
            from app.analytics.war.redraft.service import WARService
            from app.services.war.shared import build_shared_redraft_war_by_league_id

            war_service = WARService()
            war_by_league_id = await build_shared_redraft_war_by_league_id(
                db=db,
                redis=redis,
                leagues=leagues,
                war_service=war_service,
            )
        except Exception as exc:
            logger.warning("Could not calculate shared WAR for weekly metrics: %s", exc)
            war_by_league_id = {}

    async def _fetch_matchup(league: League, week: int):
        try:
            raw_matchups = await sleeper.read.get_matchups(league.league_id, week)
            return (league, week, raw_matchups)
        except Exception as exc:
            logger.warning(
                "Failed to fetch matchups for league %s week %s: %s",
                league.league_id,
                week,
                exc,
            )
            return (league, week, None)

    results = await bounded_gather(
        [
            _fetch_matchup(league, week)
            for league, week in fetch_tasks
        ],
        limit=10,
    )

    # Collect all player_ids referenced across all fetched matchups
    all_player_ids: set[str] = set()
    for _, _, raw_matchups in results:
        if not raw_matchups:
            continue
        for m in raw_matchups:
            players_list = getattr(m, "players", None) or (m.get("players") if isinstance(m, dict) else [])
            players_points = getattr(m, "players_points", None) or (m.get("players_points") if isinstance(m, dict) else {})
            all_player_ids.update(players_list or [])
            all_player_ids.update(players_points.keys())

    # Bulk query positions and player values
    player_positions: dict[str, str] = {}
    if all_player_ids:
        pos_result = await db.execute(
            select(Player.player_id, Player.position).where(
                col(Player.player_id).in_(list(all_player_ids))
            )
        )
        player_positions = {
            pid: pos
            for pid, pos in pos_result.all()
            if pos is not None
        }

    # Fetch enriched market values
    player_values = await get_player_values(
        db,
        player_ids=list(all_player_ids),
        redraft_war_players=[],
        value_context="redraft",
    )
    val_by_id = {v.player_id: v for v in player_values}

    rows_to_insert: list[dict[str, Any]] = []

    for league, week, raw_matchups in results:
        if not raw_matchups:
            continue

        league_war = (war_by_league_id or {}).get(league.league_id, [])
        war_by_pid = {p.player_id: p for p in league_war}

        # Group matchups to compute head-to-head outcomes
        matchups_by_id: dict[int, list[Any]] = {}
        parsed_matchups: list[dict[str, Any]] = []

        for m in raw_matchups:
            roster_id = getattr(m, "roster_id", None) or (m.get("roster_id") if isinstance(m, dict) else None)
            if roster_id is None:
                continue
            roster_id = int(roster_id)
            matchup_id = getattr(m, "matchup_id", None) or (m.get("matchup_id") if isinstance(m, dict) else None)
            actual_points = float(getattr(m, "points", 0.0) or (m.get("points", 0.0) if isinstance(m, dict) else 0.0))
            players = getattr(m, "players", None) or (m.get("players") if isinstance(m, dict) else [])
            players_points = getattr(m, "players_points", None) or (m.get("players_points") if isinstance(m, dict) else {})

            parsed = {
                "roster_id": roster_id,
                "matchup_id": int(matchup_id) if matchup_id is not None else None,
                "points": actual_points,
                "players": list(players or []),
                "players_points": {str(k): float(v) for k, v in (players_points or {}).items()},
            }
            parsed_matchups.append(parsed)
            if parsed["matchup_id"] is not None:
                matchups_by_id.setdefault(parsed["matchup_id"], []).append(parsed)

        for item in parsed_matchups:
            roster_id = item["roster_id"]
            actual_points = item["points"]
            players = item["players"]
            players_points = item["players_points"]

            # Head to head record
            wins, losses, ties = 0, 0, 0
            matchup_id = item["matchup_id"]
            if matchup_id is not None and len(matchups_by_id.get(matchup_id, [])) == 2:
                opp = [o for o in matchups_by_id[matchup_id] if o["roster_id"] != roster_id][0]
                if actual_points > opp["points"]:
                    wins = 1
                elif actual_points < opp["points"]:
                    losses = 1
                else:
                    ties = 1

            # Optimal points
            max_points = calculate_optimal_lineup_points(
                roster_positions=league.roster_positions or [],
                players_points=players_points,
                player_positions=player_positions,
                actual_starter_points=actual_points,
            )

            # Roster valuations & WAR
            ktc_val = 0.0
            fc_val = 0.0
            roster_league_players: list[LeaguePlayer] = []

            for pid in players:
                pv = val_by_id.get(pid)
                if pv is not None:
                    ktc_val += pv.ktc_value or 0.0
                    fc_val += pv.fc_value or 0.0
                war_p = war_by_pid.get(pid)
                roster_league_players.append(
                    LeaguePlayer(
                        player_id=pid,
                        name=war_p.name if war_p else "",
                        position=player_positions.get(pid, ""),
                        projected_points=war_p.projection if war_p else 0.0,
                        redraft_starter_war=war_p.starter_war if war_p else 0.0,
                        redraft_roster_war=war_p.roster_war if war_p else 0.0,
                    )
                )

            starter_war = round(
                sum(p.redraft_starter_war or 0.0 for p in roster_league_players),
                2,
            )
            roster_war = round(
                sum(p.redraft_roster_war or 0.0 for p in roster_league_players),
                2,
            )
            sleeper_proj = calculate_projected_starter_points(
                roster_positions=league.roster_positions or [],
                players=roster_league_players,
            )

            rows_to_insert.append(
                {
                    "league_id": league.league_id,
                    "season": league.season,
                    "week": week,
                    "roster_id": roster_id,
                    "points": round(actual_points, 2),
                    "max_points": round(max_points, 2),
                    "wins": wins,
                    "losses": losses,
                    "ties": ties,
                    "starter_war": starter_war,
                    "roster_war": roster_war,
                    "sleeper_projection": round(sleeper_proj, 2),
                    "ktc_redraft": round(ktc_val, 2),
                    "fantasycalc_redraft": round(fc_val, 2),
                }
            )

    if rows_to_insert:
        await upsert_league_weekly_metrics(db, rows_to_insert)

    return len(rows_to_insert)
