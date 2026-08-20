from __future__ import annotations

import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from types import SimpleNamespace

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.analytics.war.redraft.service import (
    WARService,
    WARSharedData,
)
from app.crud.sleeper.draft import (
    get_available_stat_seasons,
    get_historical_rookie_draft_selections,
)
from app.schemas.draft import DraftPickAsset

SHARED_DATA_CACHE_KEY_PREFIX = "rookie_war:shared:"
SHARED_DATA_CACHE_TTL_SECONDS = 6 * 60 * 60


@dataclass(frozen=True)
class RookiePickWarAggregate:
    starter_war: float
    roster_war: float
    sample_size: int
    source_label: str


@dataclass
class _SharedData:
    selections: list
    players: list
    stat_seasons: list[int]


def _build_shared_cache_key(rounds: list[int]) -> str:
    return f"{SHARED_DATA_CACHE_KEY_PREFIX}:{'-'.join(str(r) for r in rounds)}"


def _sel_attr(selection, name: str):
    if isinstance(selection, dict):
        return selection.get(name)
    return getattr(selection, name, None)


async def _load_shared_data(
    db: AsyncSession,
    redis,
    *,
    rounds: list[int],
) -> _SharedData:
    if redis is not None:
        cache_key = _build_shared_cache_key(rounds)
        cached = await redis.get(cache_key)
        if cached:
            data = json.loads(cached)
            return _SharedData(
                selections=data["selections"],
                players=data["players"],
                stat_seasons=data["stat_seasons"],
            )

    t0 = time.monotonic()
    selections = await get_historical_rookie_draft_selections(
        db,
        rounds=rounds,
    )
    logger.info("rookie_war get_selections took %.1fs", time.monotonic() - t0)

    t0 = time.monotonic()
    stat_seasons = await get_available_stat_seasons(
        db,
    )
    logger.info("rookie_war get_seasons took %.1fs", time.monotonic() - t0)

    war_service = WARService()
    t0 = time.monotonic()
    players = await war_service.loader.get_players(
        db,
    )
    logger.info("rookie_war get_players took %.1fs", time.monotonic() - t0)

    shared = _SharedData(
        selections=selections,
        players=players,
        stat_seasons=stat_seasons,
    )

    if redis is not None and selections and stat_seasons and players:
        cache_key = _build_shared_cache_key(rounds)
        await redis.set(
            cache_key,
            json.dumps(
                {
                    "selections": [
                        {
                            "id": getattr(s, "id", None),
                            "player_id": getattr(s, "player_id", None),
                            "season": getattr(s, "season", None),
                            "round": getattr(s, "round", None),
                            "round_slot": getattr(s, "round_slot", None),
                        }
                        for s in selections
                    ],
                    "players": players,
                    "stat_seasons": stat_seasons,
                },
                default=str,
            ),
            ex=SHARED_DATA_CACHE_TTL_SECONDS,
        )

    return shared


async def get_rookie_pick_war_values_by_key(
    db: AsyncSession,
    *,
    picks: list[DraftPickAsset],
    league_total_rosters: int,
    league_scoring_settings: dict[str, float],
    league_roster_positions: list[str],
    redis=None,
) -> dict[tuple[str, int, int], RookiePickWarAggregate]:
    if not picks:
        return {}

    rounds = sorted(
        {
            int(pick.round)
            for pick in picks
        }
    )

    _rw_t0 = time.monotonic()
    shared = await _load_shared_data(
        db,
        redis,
        rounds=rounds,
    )
    logger.info("rookie_war shared data total took %.1fs", time.monotonic() - _rw_t0)

    selections = shared.selections
    if not selections:
        return {}

    stat_seasons = shared.stat_seasons
    if not stat_seasons:
        return {}

    latest_completed_season = max(stat_seasons)
    selections = [
        s
        for s in selections
        if int(_sel_attr(s, "season") or 0) <= latest_completed_season
    ]

    if not selections:
        return {}

    war_service = WARService()
    players = shared.players

    starter_war_by_player_id: dict[str, float] = defaultdict(float)
    roster_war_by_player_id: dict[str, float] = defaultdict(float)
    draft_year_by_player_id: dict[str, int] = {}

    for selection in selections:
        player_id = _sel_attr(selection, "player_id")
        if player_id is None:
            continue

        draft_year_by_player_id.setdefault(
            player_id,
            int(_sel_attr(selection, "season")),
        )

    for season in stat_seasons:
        _season_start = time.monotonic()
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
        logger.info(
            "rookie_war season=%s elapsed=%.1fs",
            season,
            time.monotonic() - _season_start,
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
        player_id = _sel_attr(selection, "player_id")
        if player_id is None:
            continue

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
                int(_sel_attr(selection, "round")),
                int(_sel_attr(selection, "round_slot")),
            )
        ].append(
            sample,
        )
        round_samples[
            int(_sel_attr(selection, "round"))
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
