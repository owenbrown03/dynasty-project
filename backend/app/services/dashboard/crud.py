from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.sleeper.api import (
    User,
    League,
    Roster,
)


async def get_user_by_name(
    db: AsyncSession,
    username: str,
):
    result = await db.execute(
        select(User)
        .where(
            User.display_name == username
        )
    )

    return result.scalar_one_or_none()



async def get_user_leagues(
    db: AsyncSession,
    user_id: str,
):

    result = await db.execute(
        select(
            League,
            Roster,
        )
        .join(
            Roster,
            Roster.league_id == League.league_id,
        )
        .where(
            Roster.owner_id == user_id
        )
    )


    leagues = {}


    for league, roster in result.all():

        if league.league_id not in leagues:
            leagues[league.league_id] = {
                "league": league,
                "user_rosters": [],
            }


        leagues[league.league_id][
            "user_rosters"
        ].append(
            roster
        )


    return leagues



async def get_all_league_rosters(
    db: AsyncSession,
    league_ids: list[str],
):

    result = await db.execute(
        select(Roster)
        .where(
            Roster.league_id.in_(league_ids)
        )
    )


    rosters = {}


    for roster in result.scalars():

        rosters.setdefault(
            roster.league_id,
            []
        ).append(
            roster
        )


    return rosters