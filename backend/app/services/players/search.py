from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.fc.models import FantasyCalcValue
from app.models.db.ktc.models import KTCValue
from app.models.db.sleeper import api as model
from app.models.db.underdog.models import UnderdogADP
from app.services.waivers.dynasty import (
    DYNASTY_FANTASY_POSITIONS,
)
from app.utils.age import calculate_age
from app.crud.value import _calculate_adp_value


@dataclass(frozen=True)
class LocalPlayerSearchResult:
    player_id: str
    name: str
    position: str | None
    team: str | None
    age: float | None
    ktc_value: int | None
    fc_value: int | None
    adp_value: float | None
    underdog_position_rank: str | None
    dynasty_starter_war: float | None = None
    dynasty_roster_war: float | None = None
    redraft_starter_war: float | None = None
    redraft_roster_war: float | None = None


async def search_local_dynasty_players(
    *,
    db: AsyncSession,
    query: str,
    limit: int = 10,
) -> list[LocalPlayerSearchResult]:
    search_term = query.strip()

    if len(search_term) < 2:
        return []

    player_name_expression = func.concat_ws(
        " ",
        model.Player.first_name,
        model.Player.last_name,
    )

    result = await db.execute(
        select(model.Player)
        .where(
            model.Player.position.in_(
                DYNASTY_FANTASY_POSITIONS,
            ),
            player_name_expression.ilike(
                f"%{search_term}%",
            ),
        )
        .order_by(
            model.Player.last_name,
            model.Player.first_name,
        )
        .limit(limit)
    )

    players = list(
        result.scalars(),
    )

    if not players:
        return []

    player_ids = [
        player.player_id
        for player in players
    ]

    ktc_result = await db.execute(
        select(KTCValue).where(
            KTCValue.player_id.in_(
                player_ids,
            )
        )
    )

    ktc_by_player_id = {
        value.player_id: value
        for value in ktc_result.scalars()
    }

    fc_result = await db.execute(
        select(FantasyCalcValue).where(
            FantasyCalcValue.player_id.in_(
                player_ids,
            )
        )
    )

    fc_by_player_id = {
        value.player_id: value
        for value in fc_result.scalars()
    }

    underdog_result = await db.execute(
        select(UnderdogADP)
        .where(
            UnderdogADP.player_id.in_(
                player_ids,
            )
        )
        .order_by(
            UnderdogADP.player_id,
            UnderdogADP.id.desc(),
        )
    )

    underdog_by_player_id: dict[
        str,
        UnderdogADP,
    ] = {}

    for row in underdog_result.scalars():
        if row.player_id not in underdog_by_player_id:
            underdog_by_player_id[
                row.player_id
            ] = row

    dynasty_war_by_pid: dict = {}
    redraft_war_by_pid: dict = {}
    try:
        from types import SimpleNamespace
        from app.analytics.war.redraft.singleton import war_service
        from app.services.war.shared import build_cached_dynasty_projections_by_player_id

        shared = await war_service.load_shared_data(db, 2026)
        league = SimpleNamespace(
            season="2026",
            scoring_settings={"rec": 1.0},
            roster_positions=["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "SUPER_FLEX"],
            total_rosters=12,
        )
        war_players = await war_service.calculate_with_data(league=league, shared=shared)
        redraft_war_by_pid = {p.player_id: p for p in war_players}
        dynasty_war_by_pid = await build_cached_dynasty_projections_by_player_id(
            redis=None, player_wars=war_players
        )
    except Exception:
        pass

    return [
        LocalPlayerSearchResult(
            player_id=player.player_id,
            name=player.full_name,
            position=player.position,
            team=player.team,
            age=calculate_age(
                player.birth_date,
            ),
            ktc_value=(
                ktc_by_player_id[
                    player.player_id
                ].sf_value
                if player.player_id in ktc_by_player_id
                else None
            ),
            fc_value=(
                fc_by_player_id[
                    player.player_id
                ].value
                if player.player_id in fc_by_player_id
                else None
            ),
            adp_value=(
                _calculate_adp_value(
                    underdog_by_player_id[
                        player.player_id
                    ].adp
                    if player.player_id in underdog_by_player_id
                    else None
                )
            ),
            underdog_position_rank=(
                underdog_by_player_id[
                    player.player_id
                ].position_rank
                if player.player_id in underdog_by_player_id
                else None
            ),
            dynasty_starter_war=(
                round(dynasty_war_by_pid[player.player_id].total_starter_war, 2)
                if player.player_id in dynasty_war_by_pid
                else None
            ),
            dynasty_roster_war=(
                round(dynasty_war_by_pid[player.player_id].total_roster_war, 2)
                if player.player_id in dynasty_war_by_pid
                else None
            ),
            redraft_starter_war=(
                round(redraft_war_by_pid[player.player_id].starter_war, 2)
                if player.player_id in redraft_war_by_pid
                else None
            ),
            redraft_roster_war=(
                round(redraft_war_by_pid[player.player_id].roster_war, 2)
                if player.player_id in redraft_war_by_pid
                else None
            ),
        )
        for player in players
    ]
