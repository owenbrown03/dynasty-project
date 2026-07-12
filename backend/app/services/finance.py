from __future__ import annotations

from statistics import mean

from fastapi import HTTPException, status

from app.core.context import Context
from app.crud.sleeper.personal import (
    get_commissioner_dues_by_key,
    get_finance_entries_by_key,
    upsert_finance_entry,
)
from app.crud.sleeper.roster import get_owned_roster_rows
from app.schemas.finance import (
    FinanceLeagueSeasonEntry,
    FinanceLeagueSeasonUpdate,
    FinanceSummaryResponse,
)


def _require_finance_context(
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


def calculate_projected_winnings(
    *,
    buy_in_amount: float,
    total_rosters: int,
    playoff_teams: int,
    rank: int | None,
) -> float:
    if (
        buy_in_amount <= 0
        or total_rosters <= 0
        or playoff_teams <= 0
        or rank is None
        or rank > playoff_teams
    ):
        return 0.0

    prize_pool = buy_in_amount * total_rosters
    weights = list(
        range(
            playoff_teams,
            0,
            -1,
        )
    )
    weight_total = sum(weights)
    weight = weights[rank - 1]

    return round(
        prize_pool * weight / weight_total,
        2,
    )


def _build_buy_in_by_league_season(
    dues_by_key,
) -> dict[tuple[str, str], float]:
    buy_in_by_league_season: dict[
        tuple[str, str],
        float,
    ] = {}

    for (
        league_id,
        _roster_id,
        season,
    ), record in dues_by_key.items():
        if record.buy_in_amount is None:
            continue

        buy_in_by_league_season[
            (
                league_id,
                season,
            )
        ] = record.buy_in_amount

    return buy_in_by_league_season


def _build_league_family_key_by_league_id(
    owned_rows,
) -> dict[str, str]:
    league_by_id = {
        league.league_id: league
        for _, league in owned_rows
    }
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


def _build_historical_payouts_by_family_and_rank(
    *,
    owned_rows,
    finance_entries_by_key,
    family_key_by_league_id,
) -> dict[tuple[str, int], list[float]]:
    payouts_by_family_and_rank: dict[
        tuple[str, int],
        list[float],
    ] = {}

    for roster, league in owned_rows:
        key = (
            league.league_id,
            league.season,
        )
        finance_entry = finance_entries_by_key.get(
            key,
        )

        if finance_entry is None or finance_entry.winnings_amount <= 0:
            continue

        rank = None
        if league.total_rosters > 0:
            other_rosters = [
                other_roster
                for other_roster, other_league in owned_rows
                if other_league.league_id == league.league_id
            ]
            ordered = sorted(
                other_rosters,
                key=lambda other: (
                    other.wins,
                    -other.losses,
                    other.fpts,
                    -other.roster_id,
                ),
                reverse=True,
            )
            rank = next(
                (
                    index
                    for index, other in enumerate(
                        ordered,
                        start=1,
                    )
                    if other.roster_id == roster.roster_id
                ),
                None,
            )

        if rank is None:
            continue

        payouts_by_family_and_rank.setdefault(
            (
                family_key_by_league_id[
                    league.league_id
                ],
                rank,
            ),
            [],
        ).append(
            finance_entry.winnings_amount,
        )

    return payouts_by_family_and_rank


async def get_finance_summary(
    ctx: Context,
) -> FinanceSummaryResponse:
    _require_finance_context(
        ctx,
    )

    owned_rows = await get_owned_roster_rows(
        db=ctx.db,
        connection=ctx.connection,
    )

    league_ids = [
        league.league_id
        for _, league in owned_rows
    ]
    finance_entries_by_key = await get_finance_entries_by_key(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
        league_ids=league_ids,
    )
    family_key_by_league_id = _build_league_family_key_by_league_id(
        owned_rows,
    )
    historical_payouts_by_family_and_rank = (
        _build_historical_payouts_by_family_and_rank(
            owned_rows=owned_rows,
            finance_entries_by_key=finance_entries_by_key,
            family_key_by_league_id=family_key_by_league_id,
        )
    )
    commissioner_dues_by_key = await get_commissioner_dues_by_key(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
        league_ids=league_ids,
    )
    commissioner_buy_in_by_league_season = (
        _build_buy_in_by_league_season(
            commissioner_dues_by_key,
        )
    )

    entries: list[FinanceLeagueSeasonEntry] = []

    for roster, league in owned_rows:
        key = (
            league.league_id,
            league.season,
        )
        finance_entry = finance_entries_by_key.get(
            key,
        )

        buy_in_amount = (
            finance_entry.buy_in_amount
            if finance_entry is not None
            else commissioner_buy_in_by_league_season.get(
                key,
                0.0,
            )
        )
        winnings_amount = (
            finance_entry.winnings_amount
            if finance_entry is not None
            else 0.0
        )

        rank = None
        if league.total_rosters > 0:
            # Simple in-season rank proxy using record and points-for.
            other_rosters = [
                other_roster
                for other_roster, other_league in owned_rows
                if other_league.league_id == league.league_id
            ]
            ordered = sorted(
                other_rosters,
                key=lambda other: (
                    other.wins,
                    -other.losses,
                    other.fpts,
                    -other.roster_id,
                ),
                reverse=True,
            )
            rank = next(
                (
                    index
                    for index, other in enumerate(
                        ordered,
                        start=1,
                    )
                    if other.roster_id == roster.roster_id
                ),
                None,
            )

        projected_winnings_source = "heuristic"
        family_key = family_key_by_league_id.get(
            league.league_id,
            league.league_id,
        )
        historical_payouts = (
            historical_payouts_by_family_and_rank.get(
                (
                    family_key,
                    rank,
                ),
                []
            )
            if rank is not None
            else []
        )

        if historical_payouts:
            projected_winnings_amount = round(
                mean(historical_payouts),
                2,
            )
            projected_winnings_source = "historical_rank"
        else:
            projected_winnings_amount = calculate_projected_winnings(
                buy_in_amount=buy_in_amount,
                total_rosters=league.total_rosters,
                playoff_teams=league.playoff_teams,
                rank=rank,
            )

        entries.append(
            FinanceLeagueSeasonEntry(
                league_id=league.league_id,
                league_name=league.name,
                season=league.season,
                total_rosters=league.total_rosters,
                rank=rank,
                wins=roster.wins,
                losses=roster.losses,
                points_for=round(roster.fpts, 2),
                buy_in_amount=round(buy_in_amount, 2),
                winnings_amount=round(winnings_amount, 2),
                projected_winnings_amount=projected_winnings_amount,
                projected_winnings_source=projected_winnings_source,
                net_amount=round(
                    winnings_amount - buy_in_amount,
                    2,
                ),
            )
        )

    entries.sort(
        key=lambda entry: (
            int(entry.season),
            entry.league_name.lower(),
        ),
        reverse=True,
    )

    return FinanceSummaryResponse(
        total_buy_ins=round(
            sum(entry.buy_in_amount for entry in entries),
            2,
        ),
        total_winnings=round(
            sum(entry.winnings_amount for entry in entries),
            2,
        ),
        total_net=round(
            sum(entry.net_amount for entry in entries),
            2,
        ),
        projected_current_winnings=round(
            sum(entry.projected_winnings_amount for entry in entries),
            2,
        ),
        seasons=entries,
    )


async def save_finance_entry(
    body: FinanceLeagueSeasonUpdate,
    ctx: Context,
) -> FinanceLeagueSeasonEntry:
    _require_finance_context(
        ctx,
    )

    summary = await get_finance_summary(
        ctx,
    )
    existing = next(
        (
            entry
            for entry in summary.seasons
            if entry.league_id == body.league_id
            and entry.season == body.season
        ),
        None,
    )

    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League season not available in finance tracker",
        )

    await upsert_finance_entry(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
        league_id=body.league_id,
        season=body.season,
        buy_in_amount=body.buy_in_amount,
        winnings_amount=body.winnings_amount,
    )

    updated_summary = await get_finance_summary(
        ctx,
    )
    updated = next(
        (
            entry
            for entry in updated_summary.seasons
            if entry.league_id == body.league_id
            and entry.season == body.season
        ),
        None,
    )

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Saved finance entry could not be reloaded",
        )

    return updated
