from __future__ import annotations

from collections import defaultdict

from fastapi import HTTPException, status

from app.core.context import Context
from app.crud.sleeper.draft import (
    get_traded_picks_by_league_ids,
)
from app.crud.sleeper.personal import (
    get_commissioner_dues_by_key,
    get_commissioner_notes_by_league_id,
    upsert_commissioner_dues,
    upsert_commissioner_note,
)
from app.crud.sleeper.roster import (
    get_all_rosters_by_league,
    get_owned_roster_rows,
)
from app.crud.sleeper.user import get_users
from app.schemas.commissioner import (
    CommissionerLeagueDuesEntry,
    CommissionerLeagueDuesUpdate,
    CommissionerLeagueNoteUpdate,
    CommissionerWorkspaceLeague,
    CommissionerWorkspaceResponse,
)
from app.services.draft.picks import (
    build_roster_name_by_id,
)


def _require_commissioner_workspace_context(
    ctx: Context,
) -> None:
    if ctx.site_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    if ctx.connection is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Linked Sleeper account required",
        )


async def get_commissioner_workspace(
    ctx: Context,
) -> CommissionerWorkspaceResponse:
    _require_commissioner_workspace_context(
        ctx,
    )

    owned_rows = await get_owned_roster_rows(
        db=ctx.db,
        connection=ctx.connection,
    )

    leagues_by_id = {
        league.league_id: league
        for _, league in owned_rows
    }
    league_ids = list(leagues_by_id.keys())

    notes_by_league_id = await get_commissioner_notes_by_league_id(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
        league_ids=league_ids,
    )
    dues_by_key = await get_commissioner_dues_by_key(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
        league_ids=league_ids,
    )
    rosters_by_league_id = await get_all_rosters_by_league(
        db=ctx.db,
        league_ids=league_ids,
    )
    traded_picks_by_league_id = await get_traded_picks_by_league_ids(
        ctx.db,
        league_ids,
    )

    owner_ids = {
        roster.owner_id
        for rosters in rosters_by_league_id.values()
        for roster in rosters
        if roster.owner_id
    }
    users_by_id = await get_users(
        ctx.db,
        owner_ids,
    )

    leagues: list[CommissionerWorkspaceLeague] = []

    for league_id, league in leagues_by_id.items():
        rosters = rosters_by_league_id.get(
            league_id,
            [],
        )
        roster_name_by_id = build_roster_name_by_id(
            rosters=rosters,
            users_by_id=users_by_id,
        )
        dues_counter: dict[tuple[int, str], int] = defaultdict(int)

        for traded_pick, _ in traded_picks_by_league_id.get(
            league_id,
            [],
        ):
            season = str(traded_pick.season)

            if int(season) <= int(league.season):
                continue

            dues_counter[
                (
                    int(traded_pick.og_roster_id),
                    season,
                )
            ] += 1

        dues_entries = [
            CommissionerLeagueDuesEntry(
                league_id=league_id,
                roster_id=roster_id,
                roster_name=roster_name_by_id.get(
                    roster_id,
                    f"Team {roster_id}",
                ),
                season=season,
                traded_pick_count=traded_pick_count,
                buy_in_amount=(
                    dues_by_key.get(
                        (
                            league_id,
                            roster_id,
                            season,
                        )
                    ).buy_in_amount
                    if (
                        league_id,
                        roster_id,
                        season,
                    ) in dues_by_key
                    else None
                ),
                is_paid=(
                    dues_by_key.get(
                        (
                            league_id,
                            roster_id,
                            season,
                        )
                    ).is_paid
                    if (
                        league_id,
                        roster_id,
                        season,
                    ) in dues_by_key
                    else False
                ),
                paid_at=(
                    dues_by_key.get(
                        (
                            league_id,
                            roster_id,
                            season,
                        )
                    ).paid_at
                    if (
                        league_id,
                        roster_id,
                        season,
                    ) in dues_by_key
                    else None
                ),
            )
            for (roster_id, season), traded_pick_count in sorted(
                dues_counter.items(),
                key=lambda item: (
                    int(item[0][1]),
                    item[0][0],
                ),
            )
        ]

        leagues.append(
            CommissionerWorkspaceLeague(
                league_id=league_id,
                league_name=league.name,
                league_season=league.season,
                note=(
                    notes_by_league_id.get(
                        league_id,
                    ).note
                    if league_id in notes_by_league_id
                    else ""
                ),
                dues=dues_entries,
            )
        )

    leagues.sort(
        key=lambda league: (
            league.league_name.lower(),
            league.league_id,
        )
    )

    return CommissionerWorkspaceResponse(
        leagues=leagues,
    )


async def save_commissioner_note(
    body: CommissionerLeagueNoteUpdate,
    ctx: Context,
) -> CommissionerWorkspaceLeague:
    _require_commissioner_workspace_context(
        ctx,
    )

    workspace = await get_commissioner_workspace(
        ctx,
    )
    league = next(
        (
            item
            for item in workspace.leagues
            if item.league_id == body.league_id
        ),
        None,
    )

    if league is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not available in commissioner workspace",
        )

    await upsert_commissioner_note(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
        league_id=body.league_id,
        note=body.note,
    )

    league.note = body.note
    return league


async def save_commissioner_dues(
    body: CommissionerLeagueDuesUpdate,
    ctx: Context,
) -> CommissionerLeagueDuesEntry:
    _require_commissioner_workspace_context(
        ctx,
    )

    workspace = await get_commissioner_workspace(
        ctx,
    )
    league = next(
        (
            item
            for item in workspace.leagues
            if item.league_id == body.league_id
        ),
        None,
    )

    if league is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not available in commissioner workspace",
        )

    due_entry = next(
        (
            entry
            for entry in league.dues
            if entry.roster_id == body.roster_id
            and entry.season == body.season
        ),
        None,
    )

    if due_entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dues entry not found for this league roster season",
        )

    record = await upsert_commissioner_dues(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
        league_id=body.league_id,
        roster_id=body.roster_id,
        season=body.season,
        buy_in_amount=body.buy_in_amount,
        is_paid=body.is_paid,
    )

    due_entry.buy_in_amount = record.buy_in_amount
    due_entry.is_paid = record.is_paid
    due_entry.paid_at = record.paid_at
    return due_entry
