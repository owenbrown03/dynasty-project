from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.sleeper.personal import get_hidden_league_ids
from app.schemas.league import LeagueOverviewItem
from app.services.leagues.selection import (
    get_visible_owned_league_rows_by_username,
)


async def get_league_overview(
    db: AsyncSession,
    username: str,
    *,
    site_user_id=None,
    include_hidden: bool = False,
) -> list[LeagueOverviewItem]:
    hidden_league_ids = set()

    if site_user_id is not None:
        hidden_league_ids = await get_hidden_league_ids(
            db=db,
            site_user_id=site_user_id,
        )

    leagues = await get_visible_owned_league_rows_by_username(
        db=db,
        username=username,
        site_user_id=site_user_id,
        include_hidden=include_hidden,
    )

    if not leagues:
        return []

    output = []

    for row in leagues:
        league = row.league
        output.append(
            LeagueOverviewItem(
                league_id=league.league_id,
                league_name=league.name,
                season=league.season,
                total_rosters=league.total_rosters,
                is_hidden=league.league_id in hidden_league_ids,
            )
        )

    return output
