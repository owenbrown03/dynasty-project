from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.sleeper.league import (
    get_owned_leagues_by_sleeper_user_id,
    get_user_leagues,
)
from app.crud.sleeper.personal import get_hidden_league_ids, get_league_sort_orders
from app.models.db.sleeper.api import League, Roster, User


@dataclass(frozen=True)
class OwnedLeagueRow:
    league: League
    roster: Roster


def _season_value(
    season: str | None,
) -> int:
    try:
        return int(season or 0)
    except (TypeError, ValueError):
        return 0


def _family_key_by_league_id(
    league_by_id: dict[str, League],
) -> dict[str, str]:
    family_key_by_league_id: dict[str, str] = {}

    for league_id, league in league_by_id.items():
        current = league
        visited: set[str] = set()

        while (
            current.previous_league_id
            and current.previous_league_id in league_by_id
            and current.previous_league_id not in visited
        ):
            visited.add(current.league_id)
            current = league_by_id[
                current.previous_league_id
            ]

        family_key_by_league_id[league_id] = current.league_id

    return family_key_by_league_id


def select_latest_owned_league_rows(
    owned_rows: list[OwnedLeagueRow],
    *,
    hidden_league_ids: set[str] | None = None,
    include_hidden: bool = False,
    sort_order: dict[str, int] | None = None,
) -> list[OwnedLeagueRow]:
    if not owned_rows:
        return []

    hidden_league_ids = hidden_league_ids or set()

    unique_rows_by_league_id: dict[str, OwnedLeagueRow] = {}

    for row in owned_rows:
        unique_rows_by_league_id.setdefault(
            row.league.league_id,
            row,
        )

    deduped_rows = list(
        unique_rows_by_league_id.values(),
    )
    league_by_id = {
        row.league.league_id: row.league
        for row in deduped_rows
    }
    family_key_by_league_id = _family_key_by_league_id(
        league_by_id,
    )

    max_season = max(
        _season_value(row.league.season)
        for row in deduped_rows
    )
    minimum_visible_season = max_season - 1

    latest_row_by_family: dict[str, OwnedLeagueRow] = {}

    for row in deduped_rows:
        league = row.league
        family_key = family_key_by_league_id.get(
            league.league_id,
            league.league_id,
        )
        existing = latest_row_by_family.get(
            family_key,
        )

        if existing is None or _season_value(
            league.season,
        ) > _season_value(existing.league.season):
            latest_row_by_family[family_key] = row

    filtered_rows: list[OwnedLeagueRow] = []

    for row in latest_row_by_family.values():
        league = row.league

        if _season_value(
            league.season,
        ) < minimum_visible_season:
            continue

        if (
            not include_hidden
            and league.league_id in hidden_league_ids
        ):
            continue

        filtered_rows.append(
            row,
        )

    if sort_order:
        return sorted(
            filtered_rows,
            key=lambda row: sort_order.get(
                row.league.league_id,
                9999,
            ),
        )

    return sorted(
        filtered_rows,
        key=lambda row: (
            -_season_value(row.league.season),
            row.league.name.lower(),
            row.league.league_id,
        ),
    )


async def get_visible_owned_league_rows_by_username(
    *,
    db: AsyncSession,
    username: str,
    site_user_id: UUID | None = None,
    include_hidden: bool = False,
) -> list[OwnedLeagueRow]:
    raw_rows = await get_user_leagues(
        db,
        username,
    )
    hidden_league_ids = set()
    sort_order = None

    if site_user_id is not None:
        hidden_league_ids = await get_hidden_league_ids(
            db=db,
            site_user_id=site_user_id,
        )

    user_result = await db.execute(
        select(User.user_id).where(User.display_name == username.strip())
    )
    sleeper_user_id = user_result.scalar_one_or_none()

    if sleeper_user_id:
        sort_order = await get_league_sort_orders(
            db=db,
            user_id=sleeper_user_id,
        )

    return select_latest_owned_league_rows(
        [
            OwnedLeagueRow(
                league=league,
                roster=roster,
            )
            for league, roster in raw_rows
        ],
        hidden_league_ids=hidden_league_ids,
        include_hidden=include_hidden,
        sort_order=sort_order,
    )


async def get_visible_owned_league_rows_by_sleeper_user_id(
    *,
    db: AsyncSession,
    sleeper_user_id: str,
    site_user_id: UUID | None = None,
    include_hidden: bool = False,
) -> list[OwnedLeagueRow]:
    raw_rows = await get_owned_leagues_by_sleeper_user_id(
        db,
        sleeper_user_id,
    )
    hidden_league_ids = set()
    sort_order = None

    if site_user_id is not None:
        hidden_league_ids = await get_hidden_league_ids(
            db=db,
            site_user_id=site_user_id,
        )

    sort_order = await get_league_sort_orders(
        db=db,
        user_id=sleeper_user_id,
    )

    return select_latest_owned_league_rows(
        [
            OwnedLeagueRow(
                league=league,
                roster=roster,
            )
            for league, roster in raw_rows
        ],
        hidden_league_ids=hidden_league_ids,
        include_hidden=include_hidden,
        sort_order=sort_order,
    )
