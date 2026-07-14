from typing import Iterable
import math

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.analytics.war.dynasty.models import DynastyProjection
from app.analytics.war.redraft.models import PlayerWAR
from app.models.db.fc.models import FantasyCalcValue
from app.models.db.ktc.models import KTCValue
from app.models.db.sleeper.api import Player
from app.models.db.underdog.models import UnderdogADP
from app.schemas.player import PlayerValue
from app.utils.age import calculate_age


ADP_VALUE_MAX_PICK = 400.0
ADP_VALUE_SCALE = 10000.0


def _calculate_adp_value(
    adp: float | None,
) -> float | None:
    if adp is None or adp <= 0:
        return None

    clamped_adp = min(
        max(adp, 1.0),
        ADP_VALUE_MAX_PICK,
    )
    max_log = math.log(
        ADP_VALUE_MAX_PICK + 1.0,
    )
    value = (
        (max_log - math.log(clamped_adp))
        / max_log
    ) * ADP_VALUE_SCALE

    return round(
        value,
        2,
    )


async def get_player_values(
    db: AsyncSession,
    player_ids: Iterable[str],
    redraft_war_players: list[PlayerWAR],
    dynasty_war_by_player_id: dict[str, DynastyProjection] | None = None,
) -> list[PlayerValue]:
    """
    Enriches player IDs with market values, current redraft WAR,
    and dynasty WAR.

    Redraft WAR:
        League-specific current-season value.

    Dynasty WAR:
        Future value calculated from the league-specific redraft WAR
        baseline, then adjusted for age, expected games remaining,
        aging decline, and discounting.
    """

    player_ids = list(dict.fromkeys(player_ids))

    if not player_ids:
        return []

    dynasty_war_by_player_id = dynasty_war_by_player_id or {}

    # ------------------------------------
    # Players
    # ------------------------------------
    result = await db.execute(
        select(Player).where(
            Player.player_id.in_(player_ids)
        )
    )

    players = {
        player.player_id: player
        for player in result.scalars()
    }

    # ------------------------------------
    # KTC
    # ------------------------------------
    result = await db.execute(
        select(KTCValue).where(
            KTCValue.player_id.in_(player_ids)
        )
    )

    ktc_values = {
        value.player_id: value
        for value in result.scalars()
    }

    # ------------------------------------
    # FantasyCalc
    # ------------------------------------
    result = await db.execute(
        select(FantasyCalcValue).where(
            FantasyCalcValue.player_id.in_(player_ids)
        )
    )

    fc_values = {
        value.player_id: value
        for value in result.scalars()
    }

    # ------------------------------------
    # Latest Underdog ADP
    # ------------------------------------
    result = await db.execute(
        select(UnderdogADP)
        .where(
            UnderdogADP.player_id.in_(player_ids)
        )
        .order_by(
            UnderdogADP.player_id,
            UnderdogADP.id.desc(),
        )
    )

    underdog_values: dict[str, UnderdogADP] = {}

    for row in result.scalars():
        if row.player_id not in underdog_values:
            underdog_values[row.player_id] = row

    # ------------------------------------
    # Redraft WAR lookup
    # ------------------------------------
    redraft_war_by_player_id = {
        player.player_id: player
        for player in redraft_war_players
    }

    # ------------------------------------
    # Build output
    # ------------------------------------
    output: list[PlayerValue] = []

    for player_id in player_ids:
        player = players.get(player_id)

        if player is None:
            continue

        ktc = ktc_values.get(player_id)
        fc = fc_values.get(player_id)
        underdog = underdog_values.get(player_id)

        redraft_war = redraft_war_by_player_id.get(player_id)
        dynasty_war = dynasty_war_by_player_id.get(player_id)

        output.append(
            PlayerValue(
                player_id=player_id,
                name=player.full_name,
                position=player.position,
                team=player.team,
                age=calculate_age(player.birth_date),

                ktc_value=(
                    ktc.sf_value
                    if ktc is not None
                    else None
                ),

                fc_value=(
                    fc.value
                    if fc is not None
                    else None
                ),

                adp_value=_calculate_adp_value(
                    underdog.adp
                    if underdog is not None
                    else None
                ),

                underdog_position_rank=(
                    underdog.position_rank
                    if underdog is not None
                    else None
                ),

                redraft_starter_war=(
                    redraft_war.starter_war
                    if redraft_war is not None
                    else None
                ),

                redraft_roster_war=(
                    redraft_war.roster_war
                    if redraft_war is not None
                    else None
                ),

                dynasty_starter_war=(
                    dynasty_war.total_starter_war
                    if dynasty_war is not None
                    else None
                ),

                dynasty_roster_war=(
                    dynasty_war.total_roster_war
                    if dynasty_war is not None
                    else None
                ),

                dynasty_expected_games_remaining=(
                    dynasty_war.expected_games_remaining
                    if dynasty_war is not None
                    else None
                ),

                dynasty_seasons_remaining=(
                    dynasty_war.seasons_remaining
                    if dynasty_war is not None
                    else None
                ),
            )
        )

    return output
