from __future__ import annotations

from statistics import mean

from fastapi import HTTPException, status

from app.core.context import Context
from app.crud.sleeper.personal import (
    delete_finance_entry,
    get_commissioner_dues_by_key,
    get_finance_entries_by_key,
    get_finance_league_defaults_by_family_id,
    get_finance_user_defaults,
    upsert_finance_entry,
    upsert_finance_league_default,
    upsert_finance_user_defaults,
)
from app.crud.sleeper.roster import get_owned_roster_rows
from app.schemas.finance import (
    FinanceDefaultSettings,
    FinanceLeagueDefaultEntry,
    FinanceLeagueDefaultsUpdate,
    FinanceLeagueSeasonEntry,
    FinanceLeagueSeasonUpdate,
    FinancePlacePayout,
    FinanceSeasonReset,
    FinanceSummaryResponse,
    FinanceDefaultsUpdate,
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


def calculate_rank(
    *,
    owned_rows,
    league_id: str,
    roster_id: int,
) -> int | None:
    other_rosters = [
        other_roster
        for other_roster, other_league in owned_rows
        if other_league.league_id == league_id
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
    return next(
        (
            index
            for index, other in enumerate(
                ordered,
                start=1,
            )
            if other.roster_id == roster_id
        ),
        None,
    )


def normalize_payout_structure(
    payout_structure: dict[str, float] | None,
) -> dict[str, float]:
    if not payout_structure:
        return {}

    normalized: dict[str, float] = {}

    for key, value in payout_structure.items():
        if value <= 0:
            continue

        try:
            place = int(key)
        except (
            TypeError,
            ValueError,
        ):
            continue

        if place <= 0:
            continue

        normalized[str(place)] = round(
            float(value),
            2,
        )

    return normalized


def serialize_payout_structure(
    payout_structure: dict[str, float] | None,
) -> list[FinancePlacePayout]:
    normalized = normalize_payout_structure(
        payout_structure,
    )
    return [
        FinancePlacePayout(
            place=int(place),
            amount=amount,
        )
        for place, amount in sorted(
            normalized.items(),
            key=lambda item: int(item[0]),
        )
    ]


def payout_for_rank(
    payout_structure: dict[str, float] | None,
    rank: int | None,
) -> float | None:
    if rank is None:
        return None

    normalized = normalize_payout_structure(
        payout_structure,
    )

    if str(rank) not in normalized:
        return None

    return normalized[str(rank)]


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


def _build_family_name_by_league_id(
    owned_rows,
    family_key_by_league_id: dict[str, str],
) -> dict[str, str]:
    family_name_by_key: dict[str, tuple[int, str]] = {}

    for _, league in owned_rows:
        family_key = family_key_by_league_id.get(
            league.league_id,
            league.league_id,
        )
        season_value = int(league.season)
        previous = family_name_by_key.get(
            family_key,
        )

        if previous is None or season_value >= previous[0]:
            family_name_by_key[family_key] = (
                season_value,
                league.name,
            )

    return {
        family_key: league_name
        for family_key, (_, league_name) in family_name_by_key.items()
    }


def _serialize_default_settings(
    *,
    buy_in_amount: float | None,
    payout_structure: dict[str, float] | None,
) -> FinanceDefaultSettings:
    return FinanceDefaultSettings(
        buy_in_amount=(
            round(buy_in_amount, 2)
            if buy_in_amount is not None
            else None
        ),
        payout_structure=serialize_payout_structure(
            payout_structure,
        ),
    )


def _normalize_default_buy_in(
    buy_in_amount: float | None,
) -> float | None:
    if buy_in_amount is None:
        return None

    return round(
        float(buy_in_amount),
        2,
    )


def _normalize_default_payouts(
    payout_items: list[FinancePlacePayout],
) -> dict[str, float] | None:
    normalized = normalize_payout_structure(
        {
            str(item.place): item.amount
            for item in payout_items
        }
    )
    return normalized or None


def _resolve_entry_settings(
    *,
    finance_entry,
    league_default,
    user_defaults,
    commissioner_buy_in: float | None,
) -> dict[str, object]:
    if finance_entry is not None:
        return {
            "buy_in_amount": round(
                finance_entry.buy_in_amount,
                2,
            ),
            "buy_in_source": "season_override",
            "payout_structure": normalize_payout_structure(
                finance_entry.payout_structure,
            ),
            "payout_source": "season_override",
            "is_excluded": finance_entry.is_excluded,
            "has_season_override": True,
            "manual_winnings_amount": round(
                finance_entry.winnings_amount,
                2,
            ),
        }

    if (
        league_default is not None
        and league_default.buy_in_amount is not None
    ):
        buy_in_amount = round(
            league_default.buy_in_amount,
            2,
        )
        buy_in_source = "league_default"
    elif (
        user_defaults is not None
        and user_defaults.buy_in_amount is not None
    ):
        buy_in_amount = round(
            user_defaults.buy_in_amount,
            2,
        )
        buy_in_source = "global_default"
    elif commissioner_buy_in is not None:
        buy_in_amount = round(
            commissioner_buy_in,
            2,
        )
        buy_in_source = "commissioner_dues"
    else:
        buy_in_amount = 0.0
        buy_in_source = "none"

    if (
        league_default is not None
        and league_default.payout_structure is not None
    ):
        payout_structure = normalize_payout_structure(
            league_default.payout_structure,
        )
        payout_source = "league_default"
    elif (
        user_defaults is not None
        and user_defaults.payout_structure is not None
    ):
        payout_structure = normalize_payout_structure(
            user_defaults.payout_structure,
        )
        payout_source = "global_default"
    else:
        payout_structure = {}
        payout_source = "none"

    return {
        "buy_in_amount": buy_in_amount,
        "buy_in_source": buy_in_source,
        "payout_structure": payout_structure,
        "payout_source": payout_source,
        "is_excluded": False,
        "has_season_override": False,
        "manual_winnings_amount": 0.0,
    }


def _build_historical_payouts_by_family_and_rank(
    *,
    owned_rows,
    resolved_settings_by_key,
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
        resolved = resolved_settings_by_key[key]

        if resolved["is_excluded"]:
            continue

        rank = calculate_rank(
            owned_rows=owned_rows,
            league_id=league.league_id,
            roster_id=roster.roster_id,
        )

        if rank is None:
            continue

        actual_winnings = payout_for_rank(
            resolved["payout_structure"],
            rank,
        )
        winnings_amount = round(
            (
                actual_winnings
                if actual_winnings is not None
                else resolved["manual_winnings_amount"]
            ),
            2,
        )

        if winnings_amount <= 0:
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
            winnings_amount,
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
    family_key_by_league_id = _build_league_family_key_by_league_id(
        owned_rows,
    )
    family_name_by_key = _build_family_name_by_league_id(
        owned_rows,
        family_key_by_league_id,
    )
    family_keys = list(
        family_name_by_key.keys(),
    )

    finance_entries_by_key = await get_finance_entries_by_key(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
        league_ids=league_ids,
    )
    user_defaults = await get_finance_user_defaults(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
    )
    league_defaults_by_family = (
        await get_finance_league_defaults_by_family_id(
            db=ctx.db,
            site_user_id=ctx.site_user.id,
            league_family_ids=family_keys,
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

    resolved_settings_by_key: dict[
        tuple[str, str],
        dict[str, object],
    ] = {}

    for _, league in owned_rows:
        key = (
            league.league_id,
            league.season,
        )
        family_key = family_key_by_league_id.get(
            league.league_id,
            league.league_id,
        )
        resolved_settings_by_key[key] = _resolve_entry_settings(
            finance_entry=finance_entries_by_key.get(
                key,
            ),
            league_default=league_defaults_by_family.get(
                family_key,
            ),
            user_defaults=user_defaults,
            commissioner_buy_in=(
                commissioner_buy_in_by_league_season.get(
                    key,
                )
            ),
        )

    historical_payouts_by_family_and_rank = (
        _build_historical_payouts_by_family_and_rank(
            owned_rows=owned_rows,
            resolved_settings_by_key=resolved_settings_by_key,
            family_key_by_league_id=family_key_by_league_id,
        )
    )

    entries: list[FinanceLeagueSeasonEntry] = []

    for roster, league in owned_rows:
        key = (
            league.league_id,
            league.season,
        )
        resolved = resolved_settings_by_key[key]
        family_key = family_key_by_league_id.get(
            league.league_id,
            league.league_id,
        )
        rank = (
            calculate_rank(
                owned_rows=owned_rows,
                league_id=league.league_id,
                roster_id=roster.roster_id,
            )
            if league.total_rosters > 0
            else None
        )

        configured_winnings_amount = payout_for_rank(
            resolved["payout_structure"],
            rank,
        )
        winnings_amount = round(
            (
                configured_winnings_amount
                if configured_winnings_amount is not None
                else resolved["manual_winnings_amount"]
            ),
            2,
        )

        projected_winnings_source = "heuristic"
        historical_payouts = (
            historical_payouts_by_family_and_rank.get(
                (
                    family_key,
                    rank,
                ),
                [],
            )
            if rank is not None
            else []
        )

        if configured_winnings_amount is not None:
            projected_winnings_amount = round(
                configured_winnings_amount,
                2,
            )
            projected_winnings_source = "configured_place"
        elif historical_payouts:
            projected_winnings_amount = round(
                mean(historical_payouts),
                2,
            )
            projected_winnings_source = "historical_rank"
        else:
            projected_winnings_amount = calculate_projected_winnings(
                buy_in_amount=resolved["buy_in_amount"],
                total_rosters=league.total_rosters,
                playoff_teams=league.playoff_teams,
                rank=rank,
            )

        entries.append(
            FinanceLeagueSeasonEntry(
                league_id=league.league_id,
                league_family_id=family_key,
                league_name=league.name,
                season=league.season,
                total_rosters=league.total_rosters,
                rank=rank,
                finish_place=rank,
                projected_finish_place=rank,
                wins=roster.wins,
                losses=roster.losses,
                points_for=round(roster.fpts, 2),
                buy_in_amount=round(
                    resolved["buy_in_amount"],
                    2,
                ),
                winnings_amount=winnings_amount,
                payout_structure=serialize_payout_structure(
                    resolved["payout_structure"],
                ),
                buy_in_source=resolved["buy_in_source"],
                payout_source=resolved["payout_source"],
                has_season_override=resolved["has_season_override"],
                has_league_default=family_key in league_defaults_by_family,
                is_excluded=resolved["is_excluded"],
                projected_winnings_amount=projected_winnings_amount,
                projected_winnings_source=projected_winnings_source,
                net_amount=round(
                    winnings_amount - resolved["buy_in_amount"],
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

    included_entries = [
        entry
        for entry in entries
        if not entry.is_excluded
    ]

    league_defaults = [
        FinanceLeagueDefaultEntry(
            league_family_id=family_key,
            league_name=family_name_by_key.get(
                family_key,
                family_key,
            ),
            buy_in_amount=(
                round(default.buy_in_amount, 2)
                if default.buy_in_amount is not None
                else None
            ),
            payout_structure=serialize_payout_structure(
                default.payout_structure,
            ),
        )
        for family_key, default in sorted(
            league_defaults_by_family.items(),
            key=lambda item: family_name_by_key.get(
                item[0],
                item[0],
            ).lower(),
        )
    ]

    return FinanceSummaryResponse(
        total_buy_ins=round(
            sum(entry.buy_in_amount for entry in included_entries),
            2,
        ),
        total_winnings=round(
            sum(entry.winnings_amount for entry in included_entries),
            2,
        ),
        total_net=round(
            sum(entry.net_amount for entry in included_entries),
            2,
        ),
        projected_current_winnings=round(
            sum(
                entry.projected_winnings_amount
                for entry in included_entries
            ),
            2,
        ),
        defaults=_serialize_default_settings(
            buy_in_amount=(
                user_defaults.buy_in_amount
                if user_defaults is not None
                else None
            ),
            payout_structure=(
                user_defaults.payout_structure
                if user_defaults is not None
                else None
            ),
        ),
        league_defaults=league_defaults,
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
        winnings_amount=0.0,
        payout_structure=normalize_payout_structure(
            {
                str(item.place): item.amount
                for item in body.payout_structure
            }
        ),
        is_excluded=body.is_excluded,
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


async def reset_finance_entry(
    body: FinanceSeasonReset,
    ctx: Context,
) -> FinanceLeagueSeasonEntry:
    _require_finance_context(
        ctx,
    )

    league_ids = [
        body.league_id,
    ]
    finance_entries_by_key = await get_finance_entries_by_key(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
        league_ids=league_ids,
    )
    finance_entry = finance_entries_by_key.get(
        (
            body.league_id,
            body.season,
        )
    )

    if finance_entry is not None:
        await delete_finance_entry(
            db=ctx.db,
            finance_entry=finance_entry,
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League season not available in finance tracker",
        )

    return updated


async def save_finance_defaults(
    body: FinanceDefaultsUpdate,
    ctx: Context,
) -> FinanceSummaryResponse:
    _require_finance_context(
        ctx,
    )

    await upsert_finance_user_defaults(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
        buy_in_amount=_normalize_default_buy_in(
            body.buy_in_amount,
        ),
        payout_structure=_normalize_default_payouts(
            body.payout_structure,
        ),
    )

    return await get_finance_summary(
        ctx,
    )


async def save_finance_league_defaults(
    body: FinanceLeagueDefaultsUpdate,
    ctx: Context,
) -> FinanceSummaryResponse:
    _require_finance_context(
        ctx,
    )

    if not body.league_family_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one league family is required",
        )

    summary = await get_finance_summary(
        ctx,
    )
    valid_family_ids = {
        entry.league_family_id
        for entry in summary.seasons
    }

    for league_family_id in body.league_family_ids:
        if league_family_id not in valid_family_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"League family {league_family_id} is not available "
                    "in the finance tracker"
                ),
            )

        await upsert_finance_league_default(
            db=ctx.db,
            site_user_id=ctx.site_user.id,
            league_family_id=league_family_id,
            buy_in_amount=_normalize_default_buy_in(
                body.buy_in_amount,
            ),
            payout_structure=_normalize_default_payouts(
                body.payout_structure,
            ),
        )

    return await get_finance_summary(
        ctx,
    )
