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
    get_finance_entries_by_key,
    get_finance_league_defaults_by_family_id,
    get_finance_user_defaults,
    upsert_finance_entry,
    upsert_commissioner_dues,
    upsert_commissioner_note,
    upsert_commissioner_settings,
)
from app.crud.sleeper.roster import get_all_rosters_by_league
from app.crud.sleeper.user import get_users
from app.schemas.commissioner import (
    CommissionerLeagueDuesEntry,
    CommissionerLeagueDuesUpdate,
    CommissionerLeagueNoteUpdate,
    CommissionerLeagueSettingsUpdate,
    CommissionerWorkspaceLeague,
    CommissionerWorkspaceResponse,
)
from app.services.draft.picks import (
    build_roster_name_by_id,
)
from app.services.leagues.selection import (
    get_visible_owned_league_rows_by_sleeper_user_id,
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


def _build_traded_pick_label(
    *,
    season: str,
    round_number: int,
    new_roster_id: int,
    roster_name_by_id: dict[int, str],
) -> str:
    new_owner_name = roster_name_by_id.get(
        new_roster_id,
        f"Team {new_roster_id}",
    )
    return (
        f"{season} Round {round_number} "
        f"(sent to {new_owner_name})"
    )


async def get_commissioner_workspace(
    ctx: Context,
) -> CommissionerWorkspaceResponse:
    _require_commissioner_workspace_context(
        ctx,
    )

    owned_rows = await get_visible_owned_league_rows_by_sleeper_user_id(
        db=ctx.db,
        sleeper_user_id=ctx.connection.sleeper_user_id or "",
        site_user_id=ctx.site_user.id,
        include_hidden=False,
    )

    leagues_by_id = {
        row.league.league_id: row.league
        for row in owned_rows
    }
    league_ids = list(leagues_by_id.keys())

    notes_by_league_id = await get_commissioner_notes_by_league_id(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
        league_ids=league_ids,
    )
    finance_entries_by_key = await get_finance_entries_by_key(
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

    # Build league family keys so we can look up per-family defaults.
    league_by_id = leagues_by_id
    family_key_by_league_id: dict[str, str] = {}
    for lid, league in league_by_id.items():
        current = league
        visited: set[str] = set()
        prev = getattr(current, "previous_league_id", None)
        while (
            prev
            and prev in league_by_id
            and prev not in visited
        ):
            visited.add(getattr(current, "league_id", lid))
            current = league_by_id[prev]
            prev = getattr(current, "previous_league_id", None)
        family_key_by_league_id[lid] = getattr(current, "league_id", lid)

    family_ids = list(set(family_key_by_league_id.values()))
    if hasattr(ctx.db, "execute"):
        league_defaults_by_family = await get_finance_league_defaults_by_family_id(
            db=ctx.db,
            site_user_id=ctx.site_user.id,
            league_family_ids=family_ids,
        )
    else:
        league_defaults_by_family = {}
    if hasattr(ctx.db, "execute"):
        user_defaults = await get_finance_user_defaults(
            db=ctx.db,
            site_user_id=ctx.site_user.id,
        )
    else:
        user_defaults = None

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

    for row in owned_rows:
        league_id = row.league.league_id
        league = row.league
        rosters = rosters_by_league_id.get(
            league_id,
            [],
        )
        roster_name_by_id = build_roster_name_by_id(
            rosters=rosters,
            users_by_id=users_by_id,
        )
        dues_counter: dict[tuple[int, str], int] = defaultdict(int)
        traded_pick_labels_by_key: dict[
            tuple[int, str],
            list[str],
        ] = defaultdict(list)

        for traded_pick, _ in traded_picks_by_league_id.get(
            league_id,
            [],
        ):
            season = str(traded_pick.season)
            paid_years_ahead = (
                notes_by_league_id[league_id].paid_years_ahead
                if league_id in notes_by_league_id
                else 1
            )

            if int(season) <= (
                int(league.season) + paid_years_ahead
            ):
                continue

            # Only count picks where the current seller (old_roster_id) is the
            # same as the recorded original owner (og_roster_id). This excludes
            # picks the seller had previously acquired from another roster.
            old_roster = getattr(traded_pick, 'old_roster_id', None)
            og_roster = getattr(traded_pick, 'og_roster_id', None)
            if old_roster is not None and og_roster is not None and str(old_roster) != str(og_roster):
                continue

            dues_counter[
                (
                    int(traded_pick.og_roster_id),
                    season,
                )
            ] += 1
            traded_pick_labels_by_key[
                (
                    int(traded_pick.og_roster_id),
                    season,
                )
            ].append(
                _build_traded_pick_label(
                    season=season,
                    round_number=int(traded_pick.round),
                    new_roster_id=int(traded_pick.new_roster_id),
                    roster_name_by_id=roster_name_by_id,
                )
            )

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
                traded_pick_labels=sorted(
                    traded_pick_labels_by_key.get(
                        (
                            roster_id,
                            season,
                        ),
                        [],
                    )
                ),
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
                    else (
                        finance_entries_by_key.get(
                            (
                                league_id,
                                season,
                            )
                        ).buy_in_amount
                        if (
                            league_id,
                            season,
                        ) in finance_entries_by_key
                        else (
                            league_defaults_by_family.get(
                                family_key_by_league_id.get(
                                    league_id,
                                    league_id,
                                )
                            ).buy_in_amount
                            if league_defaults_by_family.get(
                                family_key_by_league_id.get(
                                    league_id,
                                    league_id,
                                )
                            ) is not None
                            else (
                                user_defaults.buy_in_amount
                                if user_defaults is not None
                                else None
                            )
                        )
                    )
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
                paid_years_ahead=(
                    notes_by_league_id[league_id].paid_years_ahead
                    if league_id in notes_by_league_id
                    else 1
                ),
                dues=dues_entries,
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

    return league.model_copy(
        update={
            "note": body.note,
        },
    )


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

    if body.buy_in_amount is not None:
        finance_entries_by_key = await get_finance_entries_by_key(
            db=ctx.db,
            site_user_id=ctx.site_user.id,
            league_ids=[body.league_id],
        )
        finance_entry = finance_entries_by_key.get(
            (
                body.league_id,
                body.season,
            )
        )
        await upsert_finance_entry(
            db=ctx.db,
            site_user_id=ctx.site_user.id,
            league_id=body.league_id,
            season=body.season,
            buy_in_amount=body.buy_in_amount,
            winnings_amount=(
                finance_entry.winnings_amount
                if finance_entry is not None
                else 0.0
            ),
            payout_structure=(
                finance_entry.payout_structure
                if finance_entry is not None
                else {}
            ),
            is_excluded=(
                finance_entry.is_excluded
                if finance_entry is not None
                else False
            ),
        )

    return due_entry.model_copy(
        update={
            "buy_in_amount": record.buy_in_amount,
            "is_paid": record.is_paid,
            "paid_at": record.paid_at,
        },
    )


async def save_commissioner_settings(
    body: CommissionerLeagueSettingsUpdate,
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

    record = await upsert_commissioner_settings(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
        league_id=body.league_id,
        paid_years_ahead=max(0, body.paid_years_ahead),
    )

    return league.model_copy(
        update={
            "paid_years_ahead": record.paid_years_ahead,
        },
    )
