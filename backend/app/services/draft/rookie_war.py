from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from types import SimpleNamespace

from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.war.redraft.service import (
    WARService,
    WARSharedData,
)
from app.crud.sleeper.draft import (
    get_available_stat_seasons,
    get_historical_rookie_draft_selections,
)
from app.schemas.draft import DraftPickAsset


@dataclass(frozen=True)
class RookiePickWarAggregate:
    starter_war: float
    roster_war: float
    sample_size: int
    source_label: str


async def get_rookie_pick_war_values_by_key(
    db: AsyncSession,
    *,
    picks: list[DraftPickAsset],
    league_total_rosters: int,
    league_scoring_settings: dict[str, float],
    league_roster_positions: list[str],
) -> dict[tuple[str, int, int], RookiePickWarAggregate]:
    if not picks:
        return {}

    rounds = sorted(
        {
            int(pick.round)
            for pick in picks
        }
    )
    selections = await get_historical_rookie_draft_selections(
        db,
        rounds=rounds,
    )

    if not selections:
        return {}

    stat_seasons = await get_available_stat_seasons(
        db,
    )

    if not stat_seasons:
        return {}

    latest_completed_season = max(
        stat_seasons,
    )
    selections = [
        selection
        for selection in selections
        if int(selection.season) <= latest_completed_season
    ]

    if not selections:
        return {}

    war_service = WARService()
    players = await war_service.loader.get_players(
        db,
    )

    starter_war_by_player_id: dict[str, float] = defaultdict(float)
    roster_war_by_player_id: dict[str, float] = defaultdict(float)
    draft_year_by_player_id: dict[str, int] = {}

    for selection in selections:
        if selection.player_id is None:
            continue

        draft_year_by_player_id.setdefault(
            selection.player_id,
            int(selection.season),
        )

    for season in stat_seasons:
        stats_rows = await war_service.loader.get_season_stats(
            db,
            season,
        )

        if not stats_rows:
            continue

        season_results = await war_service.calculate_with_data(
            league=SimpleNamespace(
                season=str(season),
                scoring_settings=league_scoring_settings,
                roster_positions=league_roster_positions,
                total_rosters=league_total_rosters,
            ),
            shared=WARSharedData(
                players=players,
                projections=stats_rows,
            ),
        )

        result_by_player_id = {
            result.player_id: result
            for result in season_results
        }

        for player_id, draft_year in draft_year_by_player_id.items():
            if season < draft_year:
                continue

            result = result_by_player_id.get(
                player_id,
            )

            if result is None:
                continue

            starter_war_by_player_id[player_id] += (
                result.starter_war
                or 0.0
            )
            roster_war_by_player_id[player_id] += (
                result.roster_war
                or 0.0
            )

    exact_samples: dict[
        tuple[int, int],
        list[tuple[float, float]],
    ] = defaultdict(list)
    round_samples: dict[
        int,
        list[tuple[float, float]],
    ] = defaultdict(list)

    for selection in selections:
        if selection.player_id is None:
            continue

        player_id = selection.player_id
        sample = (
            starter_war_by_player_id.get(
                player_id,
                0.0,
            ),
            roster_war_by_player_id.get(
                player_id,
                0.0,
            ),
        )

        exact_samples[
            (
                int(selection.round),
                int(selection.round_slot),
            )
        ].append(
            sample,
        )
        round_samples[
            int(selection.round)
        ].append(
            sample,
        )

    resolved: dict[
        tuple[str, int, int],
        RookiePickWarAggregate,
    ] = {}

    for pick in picks:
        slot = (
            pick.slot
            if pick.slot is not None
            else pick.projected_slot
        )

        aggregate_samples: list[tuple[float, float]] | None = None
        source_label: str | None = None

        if slot is not None:
            aggregate_samples = exact_samples.get(
                (
                    int(pick.round),
                    int(slot),
                )
            )

            if aggregate_samples:
                source_label = (
                    f"Historical rookie WAR from "
                    f"{len(aggregate_samples)} past "
                    f"{pick.round}.{int(slot):02d} outcomes"
                )

        if not aggregate_samples:
            aggregate_samples = round_samples.get(
                int(pick.round),
            )

            if aggregate_samples:
                source_label = (
                    f"Historical rookie WAR from "
                    f"{len(aggregate_samples)} past "
                    f"round {pick.round} outcomes"
                )

        if not aggregate_samples or source_label is None:
            continue

        sample_count = len(
            aggregate_samples,
        )
        starter_average = sum(
            starter
            for starter, _ in aggregate_samples
        ) / sample_count
        roster_average = sum(
            roster
            for _, roster in aggregate_samples
        ) / sample_count

        resolved[
            (
                pick.season,
                pick.round,
                pick.og_roster_id,
            )
        ] = RookiePickWarAggregate(
            starter_war=round(
                starter_average,
                2,
            ),
            roster_war=round(
                roster_average,
                2,
            ),
            sample_size=sample_count,
            source_label=source_label,
        )

    return resolved
