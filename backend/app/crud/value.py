from typing import Iterable

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.sleeper.api import Player
from app.models.db.ktc.models import KTCValue
from app.models.db.underdog.models import UnderdogADP
from app.models.db.fc.models import FantasyCalcValue
from app.analytics.war.redraft.models import PlayerWAR
from app.schemas.player import PlayerValue
from app.utils.age import calculate_age


async def get_player_values(
    db: AsyncSession,
    player_ids: Iterable[str],
    war_players: list[PlayerWAR],
) -> list[PlayerValue]:


    player_ids = list(player_ids)


    if not player_ids:
        return []


    # ------------------------------------
    # Players
    # ------------------------------------

    result = await db.execute(
        select(Player)
        .where(
            Player.player_id.in_(player_ids)
        )
    )

    players = {
        p.player_id: p
        for p in result.scalars()
    }


    # ------------------------------------
    # KTC
    # ------------------------------------

    result = await db.execute(
        select(KTCValue)
        .where(
            KTCValue.player_id.in_(player_ids)
        )
    )

    ktc_values = {
        x.player_id: x
        for x in result.scalars()
    }


    # ------------------------------------
    # FantasyCalc
    # ------------------------------------

    result = await db.execute(
        select(FantasyCalcValue)
        .where(
            FantasyCalcValue.player_id.in_(player_ids)
        )
    )

    fc_values = {
        x.player_id: x
        for x in result.scalars()
    }


    # ------------------------------------
    # Underdog latest
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


    underdog_values = {}

    for row in result.scalars():

        if row.player_id not in underdog_values:
            underdog_values[row.player_id] = row



    # ------------------------------------
    # WAR
    # ------------------------------------

    war_values = {
        p.player_id: p
        for p in war_players
    }


    # ------------------------------------
    # Build output
    # ------------------------------------

    output = []


    for player_id in player_ids:

        player = players.get(player_id)

        if not player:
            continue


        ktc = ktc_values.get(player_id)
        fc = fc_values.get(player_id)
        ud = underdog_values.get(player_id)
        war = war_values.get(player_id)


        output.append(
            PlayerValue(
                player_id=player_id,

                name=player.full_name,
                position=player.position,
                team=player.team,

                age=calculate_age(
                    player.birth_date
                ),


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

                starter_war=(
                    war.starter_war
                    if war
                    else None
                ),

                roster_war=(
                    war.roster_war
                    if war
                    else None
                ),
            )
        )


    return output