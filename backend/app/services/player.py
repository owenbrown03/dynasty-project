from typing import Iterable

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.sleeper.api import Player
from app.models.db.ktc.models import KTCValue
from app.models.db.underdog.models import UnderdogADP
from app.models.db.fc.models import FantasyCalcValue
from app.schemas.player import PlayerMarketValue


async def get_player_values(
    db: AsyncSession,
    sleeper_ids: Iterable[str],
    war_players: list,
) -> list[PlayerMarketValue]:

    sleeper_ids = list(sleeper_ids)

    # ------------------------------------
    # Player records
    # ------------------------------------

    result = await db.execute(
        select(Player)
        .where(Player.player_id.in_(sleeper_ids))
    )

    players = {
        p.player_id: p
        for p in result.scalars()
    }


    # ------------------------------------
    # KTC values
    # ------------------------------------

    result = await db.execute(
        select(KTCValue)
        .where(KTCValue.player_id.in_(sleeper_ids))
    )

    ktc_values = {
        x.player_id: x
        for x in result.scalars()
    }

    # ------------------------------------
    # FantacyCalc Values
    # ------------------------------------

    result = await db.execute(
        select(FantasyCalcValue)
        .where(FantasyCalcValue.player_id.in_(sleeper_ids))
    )

    fc_values = {
        x.player_id: x
        for x in result.scalars()
    }
    

    # ------------------------------------
    # Underdog ADP
    # Latest snapshot
    # ------------------------------------

    result = await db.execute(
        select(UnderdogADP)
        .where(
            UnderdogADP.player_id.in_(sleeper_ids)
        )
        .order_by(
            UnderdogADP.id.desc()
        )
    )

    underdog_values = {}

    for row in result.scalars():
        if row.player_id not in underdog_values:
            underdog_values[row.player_id] = row


    # ------------------------------------
    # WAR results already calculated
    # ------------------------------------

    war_by_player = {
        p.player_id: p
        for p in war_players
    }


    # ------------------------------------
    # Combine
    # ------------------------------------

    output = []

    for player_id in sleeper_ids:

        player = players.get(player_id)

        if not player:
            continue

        ktc = ktc_values.get(player_id)
        fc = fc_values.get(player_id)
        ud = underdog_values.get(player_id)
        war = war_by_player.get(player_id)

        output.append(
            PlayerMarketValue(
                player_id=player_id,
                name=player.full_name,

                ktc_value=(
                    ktc.sf_value
                    if ktc
                    else None
                ),

                fc_value=(
                    fc.value
                    if fc
                    else None
                ),

                underdog_position_rank=(
                    ud.position_rank
                    if ud
                    else None
                ),

                war=(
                    war.war
                    if war
                    else None
                ),
            )
        )

    return output