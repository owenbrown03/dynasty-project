from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.sleeper.league import get_user_leagues


async def get_league_overview(
    db: AsyncSession,
    username: str,
) -> list[dict[str, str | int | None]]:
    leagues = await get_user_leagues(
        db,
        username,
    )

    if not leagues:
        return []

    seen = set()
    output = []

    for league, _ in leagues:
        if league.league_id in seen:
            continue

        seen.add(
            league.league_id
        )

        output.append(
            {
                "league_id": league.league_id,
                "league_name": league.name,
                "season": league.season,
                "total_rosters": league.total_rosters,
            }
        )

    return output
