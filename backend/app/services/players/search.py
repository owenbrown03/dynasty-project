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
        )
        for player in players
    ]
