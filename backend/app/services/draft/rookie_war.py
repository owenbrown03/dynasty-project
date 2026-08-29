from __future__ import annotations

import hashlib
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

AGGREGATE_CACHE_KEY_PREFIX = "rookie_war:aggregates:"
AGGREGATE_CACHE_VERSION = "v1"
AGGREGATE_CACHE_TTL_SECONDS = 24 * 60 * 60

HISTORY_CACHE_PREFIX = "rookie_war:history:"
HISTORY_CACHE_VERSION = "v1"
HISTORY_CACHE_TTL_SECONDS = 24 * 60 * 60

PLAYERS_CACHE_KEY = "v1"
PLAYERS_CACHE_TTL_SECONDS = 30 * 60

_war_service = WARService()
_players_cache: dict[str, tuple[float, dict]] = {}


@dataclass(frozen=True)
class RookiePickWarAggregate:
    starter_war: float
    roster_war: float
    sample_size: int
    source_label: str


@dataclass
class _SharedData:
    selections: list
    stat_seasons: list[int]


def _build_shared_cache_key(rounds: list[int] | None = None) -> str:
    if rounds:
        return f"{SHARED_DATA_CACHE_KEY_PREFIX}:{'-'.join(str(r) for r in sorted(rounds))}"
    return f"{SHARED_DATA_CACHE_KEY_PREFIX}:all"


_SEL_PLAYER_ID = 0
_SEL_SEASON = 1
_SEL_ROUND = 2
_SEL_ROUND_SLOT = 3


def _sel_attr(selection, name: str):
    if isinstance(selection, (tuple, list)):
        idx = {
            "player_id": _SEL_PLAYER_ID,
            "season": _SEL_SEASON,
            "round": _SEL_ROUND,
            "round_slot": _SEL_ROUND_SLOT,
        }.get(name)
        if idx is not None:
            return selection[idx]
        return None
    if isinstance(selection, dict):
        return selection.get(name)
    return getattr(selection, name, None)


async def _load_shared_data(
    db: AsyncSession,
    redis,
    *,
    rounds: list[int] | None = None,
) -> _SharedData:
    if redis is not None:
        cache_key = _build_shared_cache_key(rounds)
        cached = await redis.get(cache_key)
        if cached:
            data = json.loads(cached)
            return _SharedData(
                selections=[
                    tuple(s) if isinstance(s, list) else s
                    for s in data["selections"]
                ],
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

    shared = _SharedData(
        selections=selections,
        stat_seasons=stat_seasons,
    )

    if redis is not None and selections and stat_seasons:
        cache_key = _build_shared_cache_key(rounds)
        await redis.set(
            cache_key,
            json.dumps(
                {
                    "selections": selections,
                    "stat_seasons": stat_seasons,
                },
                default=str,
            ),
            ttl_seconds=SHARED_DATA_CACHE_TTL_SECONDS,
        )

    return shared


async def _get_cached_players(
    db: AsyncSession,
) -> dict:
    now = time.monotonic()
    entry = _players_cache.get(PLAYERS_CACHE_KEY)

    if entry is not None and entry[0] > now:
        return entry[1]

    players = await _war_service.loader.get_players(db)
    _players_cache[PLAYERS_CACHE_KEY] = (
        now + PLAYERS_CACHE_TTL_SECONDS,
        players,
    )
    return players


def build_rookie_war_config_fingerprint(
    *,
    league_total_rosters: int,
    league_scoring_settings: dict[str, float],
    league_roster_positions: list[str],
    rounds: list[int],
    seasons: list[str],
    effective_slots: list[int],
    latest_completed_season: int,
) -> str:
    payload = json.dumps(
        {
            "total_rosters": league_total_rosters,
            "scoring_settings": league_scoring_settings,
            "roster_positions": league_roster_positions,
            "rounds": rounds,
            "seasons": seasons,
            "effective_slots": effective_slots,
            "latest_completed_season": latest_completed_season,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def _build_aggregate_cache_key(fingerprint: str) -> str:
    return (
        f"{AGGREGATE_CACHE_KEY_PREFIX}"
        f"{AGGREGATE_CACHE_VERSION}:{fingerprint}"
    )


def _serialize_aggregates(
    resolved: dict[tuple[str, int, int], RookiePickWarAggregate],
) -> list[list]:
    return [
        [
            season,
            round_number,
            og_roster_id,
            aggregate.starter_war,
            aggregate.roster_war,
            aggregate.sample_size,
            aggregate.source_label,
        ]
        for (
            (season, round_number, og_roster_id),
            aggregate,
        ) in resolved.items()
    ]


def _deserialize_aggregates(rows: list[list]) -> dict[
    tuple[str, int, int],
    RookiePickWarAggregate,
]:
    resolved: dict[
        tuple[str, int, int],
        RookiePickWarAggregate,
    ] = {}

    for (
        season,
        round_number,
        og_roster_id,
        starter_war,
        roster_war,
        sample_size,
        source_label,
    ) in rows:
        resolved[(season, round_number, og_roster_id)] = (
            RookiePickWarAggregate(
                starter_war=starter_war,
                roster_war=roster_war,
                sample_size=sample_size,
                source_label=source_label,
            )
        )

    return resolved


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

    def _effective_slot(pick) -> int:
        if pick.slot is not None:
            return int(pick.slot)
        if pick.projected_slot is not None:
            return int(pick.projected_slot)
        return 0

    fingerprint = build_rookie_war_config_fingerprint(
        league_total_rosters=league_total_rosters,
        league_scoring_settings=dict(league_scoring_settings or {}),
        league_roster_positions=list(league_roster_positions or []),
        rounds=rounds,
        seasons=sorted({str(pick.season) for pick in picks}),
        effective_slots=sorted(
            {_effective_slot(pick) for pick in picks}
        ),
        latest_completed_season=latest_completed_season,
    )
    aggregate_cache_key = _build_aggregate_cache_key(fingerprint)

    if redis is not None:
        cached_aggregates = await redis.get(aggregate_cache_key)
        if cached_aggregates:
            return _deserialize_aggregates(
                json.loads(cached_aggregates),
            )

    t0 = time.monotonic()
    players = await _get_cached_players(db)
    logger.info("rookie_war get_players took %.1fs", time.monotonic() - t0)

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
        stats_rows = await _war_service.loader.get_season_stats(
            db,
            season,
        )

        if not stats_rows:
            continue

        season_results = await _war_service.calculate_with_data(
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

    if redis is not None and resolved:
        await redis.set(
            aggregate_cache_key,
            json.dumps(_serialize_aggregates(resolved)),
            ttl_seconds=AGGREGATE_CACHE_TTL_SECONDS,
        )

    return resolved


def _build_history_cache_key(
    league_id: str,
    rounds: list[int] | None = None,
) -> str:
    rounds_suffix = "-".join(str(r) for r in sorted(rounds)) if rounds else "all"
    return (
        f"{HISTORY_CACHE_PREFIX}"
        f"{HISTORY_CACHE_VERSION}:{league_id}:"
        f"{rounds_suffix}"
    )



async def get_rookie_war_history(
    db: AsyncSession,
    redis,
    *,
    league: object | None,
    rounds: list[int] | None = None,
) -> list[dict]:
    shared = await _load_shared_data(
        db,
        redis,
        rounds=rounds,
    )

    selections = [
        s
        for s in (shared.selections or [])
        if _sel_attr(s, "player_id") is not None
    ]

    stat_seasons = shared.stat_seasons or []
    latest_completed_season = (
        max(stat_seasons) if stat_seasons else 0
    )
    selections = [
        s
        for s in selections
        if int(_sel_attr(s, "season") or 0) <= latest_completed_season
    ]

    if not selections:
        return []

    players = await _get_cached_players(
        db,
    )

    def _player_info(
        player_id: str,
    ) -> dict:
        player = players.get(
            player_id,
        )
        if player is None:
            return {
                "name": player_id,
                "position": None,
                "team": None,
            }
        return {
            "name": (
                getattr(player, "full_name", None)
                or getattr(player, "name", None)
                or player_id
            ),
            "position": getattr(
                player,
                "position",
                None,
            ),
            "team": getattr(
                player,
                "team",
                None,
            ),
        }

    draft_year_by_player_id: dict[
        str,
        int,
    ] = {}
    for selection in selections:
        player_id = _sel_attr(
            selection,
            "player_id",
        )
        draft_year_by_player_id.setdefault(
            player_id,
            int(
                _sel_attr(selection, "season") or 0
            ),
        )

    starter_war_by_player_id: dict[
        str,
        float,
    ] = defaultdict(float)
    roster_war_by_player_id: dict[
        str,
        float,
    ] = defaultdict(float)

    history_cache_key: str | None = None

    if league is not None:
        league_id = str(
            getattr(league, "league_id", "canonical")
        )
        history_cache_key = _build_history_cache_key(
            league_id,
            rounds or [],
        )

        if redis is not None:
            cached = await redis.get(
                history_cache_key,
            )
            if cached:
                cached_rows = json.loads(
                    cached,
                )
                return [
                    {
                        "player_id": row[0],
                        "name": row[1],
                        "position": row[2],
                        "team": row[3],
                        "draft_year": row[4],
                        "round": row[5],
                        "round_slot": row[6],
                        "starter_war": row[7],
                        "roster_war": row[8],
                    }
                    for row in cached_rows
                ]

        league_settings = {
            "scoring_settings": (
                getattr(league, "scoring_settings", None)
                or {}
            ),
            "roster_positions": list(
                getattr(league, "roster_positions", None)
                or []
            ),
            "total_rosters": int(
                getattr(league, "total_rosters", 0) or 0
            ),
        }

        for season in stat_seasons:
            stats_rows = await _war_service.loader.get_season_stats(
                db,
                season,
            )
            if not stats_rows:
                continue

            season_results = await _war_service.calculate_with_data(
                league=SimpleNamespace(
                    season=str(season),
                    scoring_settings=league_settings[
                        "scoring_settings"
                    ],
                    roster_positions=league_settings[
                        "roster_positions"
                    ],
                    total_rosters=league_settings[
                        "total_rosters"
                    ],
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

            for (
                player_id,
                draft_year,
            ) in draft_year_by_player_id.items():
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

    has_war = league is not None

    rows: list[dict] = []
    for selection in selections:
        player_id = _sel_attr(
            selection,
            "player_id",
        )
        info = _player_info(
            player_id,
        )
        rows.append(
            {
                "player_id": player_id,
                "name": info["name"],
                "position": info["position"],
                "team": info["team"],
                "draft_year": int(
                    _sel_attr(selection, "season") or 0
                ),
                "round": int(
                    _sel_attr(selection, "round") or 0
                ),
                "round_slot": int(
                    _sel_attr(selection, "round_slot") or 0
                ),
                "starter_war": (
                    round(
                        starter_war_by_player_id.get(
                            player_id,
                            0.0,
                        ),
                        2,
                    )
                    if has_war
                    else None
                ),
                "roster_war": (
                    round(
                        roster_war_by_player_id.get(
                            player_id,
                            0.0,
                        ),
                        2,
                    )
                    if has_war
                    else None
                ),
            }
        )

    if (
        has_war
        and history_cache_key is not None
        and redis is not None
        and rows
    ):
        await redis.set(
            history_cache_key,
            json.dumps(
                [
                    [
                        row["player_id"],
                        row["name"],
                        row["position"],
                        row["team"],
                        row["draft_year"],
                        row["round"],
                        row["round_slot"],
                        row["starter_war"],
                        row["roster_war"],
                    ]
                    for row in rows
                ]
            ),
            ttl_seconds=HISTORY_CACHE_TTL_SECONDS,
        )

    return rows
