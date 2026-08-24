from __future__ import annotations

import hashlib
import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from time import perf_counter
from types import SimpleNamespace

from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.war.dynasty.factory import build_dynasty_war_service
from app.analytics.war.redraft.service import WARSharedData
from app.analytics.war.redraft.singleton import war_service
from app.core.context import Context
from app.models.db.sleeper.api import Player
from app.models.db.underdog.models import UnderdogADP
from app.models.db.sleeper.personal import PersonalRankCurve
from app.crud.sleeper.personal import (
    get_personal_projection_outcomes,
    get_personal_projections_for_player,
    get_personal_projections_for_site_user,
    get_personal_rank_curve_rows,
    replace_personal_rank_curve_rows,
    upsert_personal_projection,
    delete_personal_projections,
)
from app.crud.value import get_player_values
from app.infrastructure.redis.client import RedisClient
from app.schemas.player import PlayerValue
from app.schemas.personal_values import (
    PersonalProjectionSeasonItem,
    PersonalValueDetailResponse,
    PersonalValueRankingEntry,
    PersonalValueRankingsResponse,
    PersonalValueRankingOutcome,
    PersonalValueRankingsUpdateRequest,
    PersonalValueRankingsUpdateResponse,
    PersonalValueRankingsResetRequest,
    PersonalValueRankingsResetResponse,
    PersonalValueUnderdogSyncRequest,
    PersonalValueLeagueContext,
    PersonalValueMetrics,
    PersonalValuePlayer,
    PersonalValuePoolGroup,
    PersonalValuePoolItem,
    PersonalValuePoolResponse,
    PersonalValueSearchResult,
    PersonalValueUpdateRequest,
)
from app.services.leagues.selection import (
    get_visible_owned_league_rows_by_sleeper_user_id,
)
from app.services.players.search import (
    search_local_dynasty_players,
)
from app.services.personal_value_projections import (
    CORE_DYNASTY_POSITIONS,
    DYNASTY_POSITIONS,
    build_default_projection_seasons as _build_default_projection_seasons,
    get_projection_end_season as _get_projection_end_season,
    merge_saved_projection_seasons as _merge_saved_projection_seasons,
    project_custom_dynasty_war as _project_custom_dynasty_war,
    validate_projection_update as _validate_projection_update,
)
from app.services.waivers.dynasty import build_dynasty_projection
from app.utils.age import calculate_age

logger = logging.getLogger(__name__)
CURVE_VERSION = "league_context_v1"
CURVE_BAND_RADIUS = 5
HISTORICAL_LOOKBACK_SEASONS = 5
PERSONAL_VALUE_HYDRATION_CACHE_TTL_SECONDS = (
    6 * 60 * 60
)
PERSONAL_VALUE_HYDRATION_CACHE_VERSION = "v1"
POOL_POSITIONS = list(CORE_DYNASTY_POSITIONS)


@dataclass(frozen=True)
class _CurveValue:
    redraft_starter_war: float
    redraft_roster_war: float


@dataclass(frozen=True)
class _ProjectionContext:
    seasons: list[PersonalProjectionSeasonItem]
    custom_values: PersonalValueMetrics
    is_customized: bool


@dataclass(frozen=True)
class _MarketSnapshot:
    metrics: PersonalValueMetrics
    ktc_value: float | None
    fc_value: float | None
    adp_value: float | None


def _require_personal_values_context(
    ctx: Context,
) -> None:
    if ctx.site_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    if (
        ctx.connection is None
        or not ctx.connection.sleeper_user_id
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Linked Sleeper account required.",
        )


def _build_settings_fingerprint(
    *,
    total_rosters: int,
    scoring_settings: dict,
    roster_positions: list[str],
) -> str:
    return json.dumps(
        {
            "total_rosters": total_rosters,
            "scoring_settings": scoring_settings,
            "roster_positions": roster_positions,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _build_personal_projection_stamp(
    *,
    saved_projections: list,
) -> str:
    if not saved_projections:
        return "none"

    ordered_rows = sorted(
        saved_projections,
        key=lambda projection: (
            projection.player_id,
            projection.season,
        ),
    )
    return "|".join(
        f"{projection.player_id}:{projection.season}:"
        f"{projection.updated_at.isoformat()}"
        for projection in ordered_rows
    )


def _build_personal_player_values_signature(
    *,
    player_values: list[PlayerValue],
) -> str:
    digest = hashlib.sha256()
    digest.update(
        json.dumps(
            [
                {
                    "player_id": player.player_id,
                    "position": player.position,
                    "age": player.age,
                    "underdog_position_rank": (
                        player.underdog_position_rank
                    ),
                    "redraft_starter_war": (
                        player.redraft_starter_war
                    ),
                    "redraft_roster_war": (
                        player.redraft_roster_war
                    ),
                    "dynasty_starter_war": (
                        player.dynasty_starter_war
                    ),
                    "dynasty_roster_war": (
                        player.dynasty_roster_war
                    ),
                }
                for player in player_values
            ],
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    return digest.hexdigest()


def _build_personal_value_hydration_cache_key(
    *,
    site_user_id,
    league,
    player_values: list[PlayerValue],
    saved_projections: list,
) -> str:
    settings_fingerprint = _build_settings_fingerprint(
        total_rosters=league.total_rosters,
        scoring_settings=league.scoring_settings or {},
        roster_positions=league.roster_positions or [],
    )
    settings_hash = hashlib.sha256(
        settings_fingerprint.encode("utf-8")
    ).hexdigest()
    projection_hash = hashlib.sha256(
        _build_personal_projection_stamp(
            saved_projections=saved_projections,
        ).encode("utf-8")
    ).hexdigest()

    return (
        "personal-value-hydration:"
        f"{PERSONAL_VALUE_HYDRATION_CACHE_VERSION}:"
        f"{site_user_id}:{league.season}:{settings_hash}:"
        f"{projection_hash}:"
        f"{_build_personal_player_values_signature(player_values=player_values)}"
    )


def _parse_position_rank(
    position: str,
    underdog_position_rank: str | None,
) -> int | None:
    if not underdog_position_rank:
        return None

    normalized = underdog_position_rank.strip().upper()

    if not normalized.startswith(position.upper()):
        return None

    raw_rank = normalized[len(position):]

    try:
        value = int(raw_rank)
    except (TypeError, ValueError):
        return None

    return value if value > 0 else None


async def _load_player_with_underdog_rank(
    *,
    ctx: Context,
    player_id: str,
) -> tuple[Player, str | None]:
    player = await ctx.db.get(
        Player,
        player_id,
    )

    if player is None or player.position not in DYNASTY_POSITIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found.",
        )

    result = await ctx.db.execute(
        select(UnderdogADP)
        .where(
            UnderdogADP.player_id == player_id,
        )
        .order_by(
            desc(UnderdogADP.id),
        )
        .limit(1)
    )
    underdog = result.scalar_one_or_none()

    return (
        player,
        underdog.position_rank
        if underdog is not None
        else None,
    )


async def _resolve_league_context(
    *,
    ctx: Context,
    league_id: str,
):
    rows = await get_visible_owned_league_rows_by_sleeper_user_id(
        db=ctx.db,
        sleeper_user_id=ctx.connection.sleeper_user_id,
        site_user_id=ctx.site_user.id,
        include_hidden=False,
    )

    target = next(
        (
            row
            for row in rows
            if row.league.league_id == league_id
        ),
        None,
    )

    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League context not found.",
        )

    return target.league


def _build_curve_lookup(
    rows: list[PersonalRankCurve],
) -> dict[str, list[PersonalRankCurve]]:
    output: dict[str, list[PersonalRankCurve]] = defaultdict(list)

    for row in rows:
        output[row.position].append(row)

    for position_rows in output.values():
        position_rows.sort(
            key=lambda row: row.rank_value,
        )

    return dict(output)


def _round_metric(
    value: float | None,
) -> float | None:
    if value is None:
        return None

    return round(float(value), 2)


def _subtract_metric(
    left: float | None,
    right: float | None,
) -> float | None:
    if left is None or right is None:
        return None

    return round(left - right, 2)


def _lookup_curve_value(
    *,
    curve_rows_by_position: dict,
    position: str,
    position_rank: int,
) -> _CurveValue | None:
    pos_data = curve_rows_by_position.get(position)
    if not pos_data:
        return None

    if isinstance(pos_data, tuple):
        lookup, pos_rows, ranks = pos_data
        
        # 1. Fast exact-match lookup (O(1))
        val = lookup.get(position_rank)
        if val is not None:
            return val
            
        # 2. Binary search fallback for closest rank (O(log N))
        import bisect
        idx = bisect.bisect_left(ranks, position_rank)
        if idx == 0:
            best = pos_rows[0]
        elif idx == len(pos_rows):
            best = pos_rows[-1]
        else:
            before = pos_rows[idx - 1]
            after = pos_rows[idx]
            if abs(before.rank_value - position_rank) <= abs(after.rank_value - position_rank):
                best = before
            else:
                best = after
        return _CurveValue(
            redraft_starter_war=best.avg_redraft_starter_war,
            redraft_roster_war=best.avg_redraft_roster_war,
        )

    # Legacy O(N) fallback path
    rows = pos_data
    best = min(
        rows,
        key=lambda row: abs(
            row.rank_value - position_rank,
        ),
    )

    return _CurveValue(
        redraft_starter_war=best.avg_redraft_starter_war,
        redraft_roster_war=best.avg_redraft_roster_war,
    )



def _weighted_redraft_values(
    *,
    curve_rows_by_position: dict,
    position: str,
    outcomes,
) -> _CurveValue | None:
    if not outcomes:
        return None

    starter_total = 0.0
    roster_total = 0.0
    total_probability = 0.0

    for outcome in outcomes:
        curve_value = _lookup_curve_value(
            curve_rows_by_position=curve_rows_by_position,
            position=position,
            position_rank=outcome.position_rank,
        )

        if curve_value is None:
            continue

        weight = float(outcome.probability) / 100.0
        total_probability += weight
        starter_total += (
            curve_value.redraft_starter_war * weight
        )
        roster_total += (
            curve_value.redraft_roster_war * weight
        )

    if total_probability <= 0:
        return None

    return _CurveValue(
        redraft_starter_war=round(
            starter_total / total_probability,
            2,
        ),
        redraft_roster_war=round(
            roster_total / total_probability,
            2,
        ),
    )


def _compute_custom_metrics(
    *,
    position: str,
    age: float | None,
    seasons: list[PersonalProjectionSeasonItem],
    current_season: int,
    curve_rows_by_position: dict,
) -> PersonalValueMetrics:
    current_projection = next(
        (
            season_item
            for season_item in seasons
            if season_item.season == current_season
        ),
        None,
    )

    current_redraft = (
        _weighted_redraft_values(
            curve_rows_by_position=curve_rows_by_position,
            position=position,
            outcomes=current_projection.outcomes,
        )
        if current_projection is not None
        else None
    )

    dynasty_redraft_by_season: dict[int, float] = {}
    dynasty_roster_by_season: dict[int, float] = {}

    for season_item in seasons:
        weighted = _weighted_redraft_values(
            curve_rows_by_position=curve_rows_by_position,
            position=position,
            outcomes=season_item.outcomes,
        )

        if weighted is None:
            continue

        dynasty_redraft_by_season[
            season_item.season
        ] = weighted.redraft_starter_war
        dynasty_roster_by_season[
            season_item.season
        ] = weighted.redraft_roster_war

    return PersonalValueMetrics(
        redraft_starter_war=(
            current_redraft.redraft_starter_war
            if current_redraft is not None
            else None
        ),
        redraft_roster_war=(
            current_redraft.redraft_roster_war
            if current_redraft is not None
            else None
        ),
        dynasty_starter_war=_project_custom_dynasty_war(
            age=age,
            position=position,
            current_season=current_season,
            season_values=dynasty_redraft_by_season,
        ),
        dynasty_roster_war=_project_custom_dynasty_war(
            age=age,
            position=position,
            current_season=current_season,
            season_values=dynasty_roster_by_season,
        ),
    )


async def _ensure_personal_rank_curve(
    *,
    db: AsyncSession,
    league,
) -> dict[str, list[PersonalRankCurve]]:
    settings_fingerprint = _build_settings_fingerprint(
        total_rosters=league.total_rosters,
        scoring_settings=league.scoring_settings,
        roster_positions=league.roster_positions,
    )
    existing = await get_personal_rank_curve_rows(
        db=db,
        settings_fingerprint=settings_fingerprint,
        curve_version=CURVE_VERSION,
    )

    if existing:
        return _build_curve_lookup(existing)

    season_end = int(league.season) - 1
    season_start = max(
        season_end - HISTORICAL_LOOKBACK_SEASONS + 1,
        2018,
    )

    players = await war_service.loader.get_players(
        db,
    )
    ranked_by_position: dict[str, dict[int, list[tuple[float, float]]]] = {
        position: defaultdict(list)
        for position in DYNASTY_POSITIONS
    }

    for season in range(
        season_start,
        season_end + 1,
    ):
        stats_rows = await war_service.loader.get_season_stats(
            db,
            season,
        )

        if not stats_rows:
            continue

        shared = WARSharedData(
            players=players,
            projections=stats_rows,
        )
        history_league = SimpleNamespace(
            season=season,
            total_rosters=league.total_rosters,
            scoring_settings=league.scoring_settings,
            roster_positions=league.roster_positions,
        )
        war_players = await war_service.calculate_with_data(
            league=history_league,
            shared=shared,
        )

        for position in DYNASTY_POSITIONS:
            position_players = sorted(
                [
                    player
                    for player in war_players
                    if player.position == position
                ],
                key=lambda player: (
                    player.projection,
                    player.player_id,
                ),
                reverse=True,
            )

            for index, player in enumerate(
                position_players,
                start=1,
            ):
                ranked_by_position[position][index].append(
                    (
                        float(player.starter_war or 0.0),
                        float(player.roster_war or 0.0),
                    )
                )

    curve_rows: list[PersonalRankCurve] = []

    for position, ranks in ranked_by_position.items():
        if not ranks:
            continue

        max_rank = max(ranks)

        for rank_value in range(1, max_rank + 1):
            band_start = max(
                1,
                rank_value - CURVE_BAND_RADIUS,
            )
            band_end = rank_value + CURVE_BAND_RADIUS
            samples = [
                sample
                for lookup_rank, values in ranks.items()
                if band_start <= lookup_rank <= band_end
                for sample in values
            ]

            if not samples:
                continue

            curve_rows.append(
                PersonalRankCurve(
                    settings_fingerprint=settings_fingerprint,
                    total_rosters=league.total_rosters,
                    scoring_settings=league.scoring_settings,
                    roster_positions=league.roster_positions,
                    season_start=season_start,
                    season_end=season_end,
                    position=position,
                    rank_value=rank_value,
                    rank_band_start=band_start,
                    rank_band_end=band_end,
                    sample_size=len(samples),
                    avg_redraft_starter_war=round(
                        sum(
                            starter
                            for starter, _ in samples
                        ) / len(samples),
                        4,
                    ),
                    avg_redraft_roster_war=round(
                        sum(
                            roster
                            for _, roster in samples
                        ) / len(samples),
                        4,
                    ),
                    curve_version=CURVE_VERSION,
                )
            )

    if not curve_rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough historical data to build a personal value curve for this league context.",
        )

    await replace_personal_rank_curve_rows(
        db=db,
        settings_fingerprint=settings_fingerprint,
        curve_version=CURVE_VERSION,
        rows=curve_rows,
    )

    return _build_curve_lookup(curve_rows)


async def _load_market_values_by_player_id(
    *,
    ctx: Context,
    league,
    player_ids: list[str] | None = None,
    value_context: str = "dynasty",
) -> dict[str, _MarketSnapshot]:
    shared = await war_service.load_shared_data(
        ctx.db,
        int(league.season),
    )
    war_players = await war_service.calculate_with_data(
        league=league,
        shared=shared,
    )

    if player_ids is not None:
        player_ids_set = set(player_ids)
        war_players = [
            player
            for player in war_players
            if player.player_id in player_ids_set
        ]

    dynasty_service = build_dynasty_war_service()
    dynasty_war_by_player_id = {}

    for war_player in war_players:
        projection = build_dynasty_projection(
            dynasty_service=dynasty_service,
            player_war=war_player,
        )

        if projection is not None:
            dynasty_war_by_player_id[
                war_player.player_id
            ] = projection

    values = await get_player_values(
        ctx.db,
        player_ids=[
            player.player_id
            for player in war_players
        ],
        redraft_war_players=war_players,
        dynasty_war_by_player_id=dynasty_war_by_player_id,
        value_context=value_context,
    )

    return {
        value.player_id: _MarketSnapshot(
            metrics=PersonalValueMetrics(
                redraft_starter_war=_round_metric(
                    value.redraft_starter_war,
                ),
                redraft_roster_war=_round_metric(
                    value.redraft_roster_war,
                ),
                dynasty_starter_war=_round_metric(
                    value.dynasty_starter_war,
                ),
                dynasty_roster_war=_round_metric(
                    value.dynasty_roster_war,
                ),
            ),
            ktc_value=(
                float(value.ktc_value)
                if value.ktc_value is not None
                else None
            ),
            fc_value=(
                float(value.fc_value)
                if value.fc_value is not None
                else None
            ),
            adp_value=(
                float(value.adp_value)
                if value.adp_value is not None
                else None
            ),
        )
        for value in values
    }


def _build_delta_values(
    *,
    custom_values: PersonalValueMetrics,
    market_values: PersonalValueMetrics,
) -> PersonalValueMetrics:
    return PersonalValueMetrics(
        redraft_starter_war=_subtract_metric(
            custom_values.redraft_starter_war,
            market_values.redraft_starter_war,
        ),
        redraft_roster_war=_subtract_metric(
            custom_values.redraft_roster_war,
            market_values.redraft_roster_war,
        ),
        dynasty_starter_war=_subtract_metric(
            custom_values.dynasty_starter_war,
            market_values.dynasty_starter_war,
        ),
        dynasty_roster_war=_subtract_metric(
            custom_values.dynasty_roster_war,
            market_values.dynasty_roster_war,
        ),
    )


def _build_projection_context(
    *,
    position: str,
    age: float | None,
    base_season: int,
    end_season: int,
    default_position_rank: int | None,
    saved_projections,
    outcomes_by_projection_id: dict[int, list],
    curve_rows_by_position: dict,
) -> _ProjectionContext:
    seasons = _merge_saved_projection_seasons(
        base_season=base_season,
        end_season=end_season,
        default_position_rank=default_position_rank,
        saved_projections=saved_projections,
        outcomes_by_projection_id=outcomes_by_projection_id,
    )
    custom_values = _compute_custom_metrics(
        position=position,
        age=age,
        seasons=seasons,
        current_season=base_season,
        curve_rows_by_position=curve_rows_by_position,
    )

    return _ProjectionContext(
        seasons=seasons,
        custom_values=custom_values,
        is_customized=any(
            season.is_customized
            for season in seasons
        ),
    )


async def hydrate_personal_player_values(
    *,
    db: AsyncSession,
    site_user_id,
    league,
    player_values: list[PlayerValue],
    redis: RedisClient | None = None,
) -> list[PlayerValue]:
    if site_user_id is None or not player_values:
        return player_values

    current_season = int(league.season)
    supported_player_ids = [
        player.player_id
        for player in player_values
        if player.position in DYNASTY_POSITIONS
    ]

    if not supported_player_ids:
        return player_values

    started_at = perf_counter()
    saved_projections = await get_personal_projections_for_site_user(
        db=db,
        site_user_id=site_user_id,
        player_ids=supported_player_ids,
    )
    cache_key = None

    if redis is not None:
        cache_key = (
            _build_personal_value_hydration_cache_key(
                site_user_id=site_user_id,
                league=league,
                player_values=player_values,
                saved_projections=saved_projections,
            )
        )
        cached_payload = await redis.get(
            cache_key,
        )

        if cached_payload:
            hydrated = [
                PlayerValue.model_validate(row)
                for row in json.loads(cached_payload)
            ]
            logger.info(
                (
                    "Personal value hydration source=redis league=%s "
                    "players=%s supported_players=%s saved_projections=%s "
                    "elapsed_ms=%.1f"
                ),
                league.league_id,
                len(player_values),
                len(supported_player_ids),
                len(saved_projections),
                (perf_counter() - started_at) * 1000,
            )
            return hydrated

    curve_rows_by_position = await _ensure_personal_rank_curve(
        db=db,
        league=league,
    )
    optimized_curve_lookup = {}
    for pos, pos_rows in curve_rows_by_position.items():
        if not pos_rows:
            continue
        lookup = {}
        for row in pos_rows:
            lookup[row.rank_value] = _CurveValue(
                redraft_starter_war=row.avg_redraft_starter_war,
                redraft_roster_war=row.avg_redraft_roster_war,
            )
        optimized_curve_lookup[pos] = (lookup, pos_rows, [r.rank_value for r in pos_rows])

    outcomes_by_projection_id = await get_personal_projection_outcomes(
        db=db,
        projection_ids=[
            projection.id
            for projection in saved_projections
            if projection.id is not None
        ],
    )
    saved_by_player_id: dict[str, list] = defaultdict(list)

    for projection in saved_projections:
        saved_by_player_id[
            projection.player_id
        ].append(projection)

    hydrated_values: list[PlayerValue] = []

    for player in player_values:
        if player.position not in DYNASTY_POSITIONS:
            hydrated_values.append(player)
            continue

        projection_context = _build_projection_context(
            position=player.position,
            age=player.age,
            base_season=current_season,
            end_season=_get_projection_end_season(
                base_season=current_season,
                age=player.age,
                position=player.position,
            ),
            default_position_rank=_parse_position_rank(
                player.position,
                player.underdog_position_rank,
            ),
            saved_projections=saved_by_player_id.get(
                player.player_id,
                [],
            ),
            outcomes_by_projection_id=outcomes_by_projection_id,
            curve_rows_by_position=optimized_curve_lookup,
        )
        hydrated_values.append(
            player.model_copy(
                update={
                    "my_redraft_starter_war": _round_metric(
                        projection_context.custom_values.redraft_starter_war,
                    ),
                    "my_redraft_roster_war": _round_metric(
                        projection_context.custom_values.redraft_roster_war,
                    ),
                    "my_dynasty_starter_war": _round_metric(
                        projection_context.custom_values.dynasty_starter_war,
                    ),
                    "my_dynasty_roster_war": _round_metric(
                        projection_context.custom_values.dynasty_roster_war,
                    ),
                },
            )
        )

    if redis is not None and cache_key is not None:
        await redis.set(
            cache_key,
            json.dumps(
                [
                    player.model_dump()
                    for player in hydrated_values
                ],
                separators=(",", ":"),
            ),
            ttl_seconds=(
                PERSONAL_VALUE_HYDRATION_CACHE_TTL_SECONDS
            ),
        )

    logger.info(
        (
            "Personal value hydration source=calculated league=%s "
            "players=%s supported_players=%s saved_projections=%s "
            "elapsed_ms=%.1f"
        ),
        league.league_id,
        len(player_values),
        len(supported_player_ids),
        len(saved_projections),
        (perf_counter() - started_at) * 1000,
    )
    return hydrated_values


async def search_personal_value_players(
    *,
    ctx: Context,
    query: str,
    league_id: str | None = None,
) -> list[PersonalValueSearchResult]:
    _require_personal_values_context(
        ctx,
    )

    results = await search_local_dynasty_players(
        db=ctx.db,
        query=query,
    )
    market_values_by_player_id: dict[str, PersonalValueMetrics] = {}
    market_snapshots_by_player_id: dict[str, _MarketSnapshot] = {}

    if league_id and results:
        league = await _resolve_league_context(
            ctx=ctx,
            league_id=league_id,
        )
        market_snapshots_by_player_id = await _load_market_values_by_player_id(
            ctx=ctx,
            league=league,
            player_ids=[
                item.player_id
                for item in results
            ],
        )

    return [
        PersonalValueSearchResult(
            player_id=item.player_id,
            name=item.name,
            position=item.position,
            team=item.team,
            age=item.age,
            underdog_position_rank=item.underdog_position_rank,
            ktc_value=item.ktc_value,
            fc_value=item.fc_value,
            adp_value=item.adp_value,
            dynasty_roster_war=(
                market_snapshots_by_player_id[
                    item.player_id
                ].metrics.dynasty_roster_war
                if item.player_id in market_snapshots_by_player_id
                else None
            ),
        )
        for item in results
    ]


async def get_personal_value_detail(
    *,
    ctx: Context,
    league_id: str,
    player_id: str,
    value_context: str = "dynasty",
) -> PersonalValueDetailResponse:
    _require_personal_values_context(
        ctx,
    )

    if value_context not in {"dynasty", "redraft"}:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=422,
            detail="value_context must be 'dynasty' or 'redraft'.",
        )

    league = await _resolve_league_context(
        ctx=ctx,
        league_id=league_id,
    )
    player, underdog_position_rank = await _load_player_with_underdog_rank(
        ctx=ctx,
        player_id=player_id,
    )
    default_position_rank = _parse_position_rank(
        player.position,
        underdog_position_rank,
    )
    current_season = int(league.season)
    end_season = _get_projection_end_season(
        base_season=current_season,
        age=calculate_age(player.birth_date),
        position=player.position,
    )

    saved = await get_personal_projections_for_player(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
        player_id=player_id,
    )
    outcomes_by_projection_id = await get_personal_projection_outcomes(
        db=ctx.db,
        projection_ids=[
            projection.id
            for projection in saved
            if projection.id is not None
        ],
    )
    curve_rows_by_position = await _ensure_personal_rank_curve(
        db=ctx.db,
        league=league,
    )
    projection_context = _build_projection_context(
        position=player.position,
        age=calculate_age(player.birth_date),
        base_season=current_season,
        end_season=end_season,
        default_position_rank=default_position_rank,
        saved_projections=saved,
        outcomes_by_projection_id=outcomes_by_projection_id,
        curve_rows_by_position=curve_rows_by_position,
    )
    market_snapshots_by_player_id = await _load_market_values_by_player_id(
        ctx=ctx,
        league=league,
        player_ids=[player.player_id],
        value_context=value_context,
    )
    market_snapshot = market_snapshots_by_player_id.get(
        player.player_id,
        _MarketSnapshot(
            metrics=PersonalValueMetrics(),
            ktc_value=None,
            fc_value=None,
            adp_value=None,
        ),
    )
    market_values = market_snapshot.metrics
    delta_values = _build_delta_values(
        custom_values=projection_context.custom_values,
        market_values=market_values,
    )

    return PersonalValueDetailResponse(
        context=PersonalValueLeagueContext(
            league_id=league.league_id,
            league_name=league.name,
            season=int(league.season),
            total_rosters=league.total_rosters,
        ),
        player=PersonalValuePlayer(
            player_id=player.player_id,
            name=player.full_name,
            position=player.position,
            team=player.team,
            age=calculate_age(player.birth_date),
            injury_status=player.injury_status,
            underdog_position_rank=underdog_position_rank,
            ktc_value=market_snapshot.ktc_value,
            fc_value=market_snapshot.fc_value,
            adp_value=market_snapshot.adp_value,
        ),
        market_values=market_values,
        custom_values=projection_context.custom_values,
        delta_values=delta_values,
        seasons=projection_context.seasons,
    )


async def get_personal_value_pool(
    *,
    ctx: Context,
    league_id: str,
    value_context: str = "dynasty",
) -> PersonalValuePoolResponse:
    _require_personal_values_context(
        ctx,
    )

    if value_context not in {"dynasty", "redraft"}:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=422,
            detail="value_context must be 'dynasty' or 'redraft'.",
        )

    league = await _resolve_league_context(
        ctx=ctx,
        league_id=league_id,
    )
    current_season = int(league.season)
    curve_rows_by_position = await _ensure_personal_rank_curve(
        db=ctx.db,
        league=league,
    )

    market_snapshots_by_player_id = await _load_market_values_by_player_id(
        ctx=ctx,
        league=league,
        value_context=value_context,
    )
    player_ids = list(
        market_snapshots_by_player_id.keys(),
    )

    if not player_ids:
        return PersonalValuePoolResponse(
            context=PersonalValueLeagueContext(
                league_id=league.league_id,
                league_name=league.name,
                season=current_season,
                total_rosters=league.total_rosters,
            ),
            groups=[],
        )

    players_result = await ctx.db.execute(
        select(Player).where(
            Player.player_id.in_(player_ids),
            Player.position.in_(DYNASTY_POSITIONS),
        )
    )
    players = {
        player.player_id: player
        for player in players_result.scalars()
    }

    underdog_result = await ctx.db.execute(
        select(UnderdogADP)
        .where(
            UnderdogADP.player_id.in_(player_ids),
        )
        .order_by(
            UnderdogADP.player_id,
            desc(UnderdogADP.id),
        )
    )
    underdog_by_player_id: dict[str, UnderdogADP] = {}

    for row in underdog_result.scalars():
        if row.player_id not in underdog_by_player_id:
            underdog_by_player_id[
                row.player_id
            ] = row

    saved_projections = await get_personal_projections_for_site_user(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
        seasons=[
            season
            for season in range(
                current_season,
                current_season + 16,
            )
        ],
    )
    saved_by_player_id: dict[str, list] = defaultdict(list)

    for projection in saved_projections:
        saved_by_player_id[
            projection.player_id
        ].append(projection)

    outcomes_by_projection_id = await get_personal_projection_outcomes(
        db=ctx.db,
        projection_ids=[
            projection.id
            for projection in saved_projections
            if projection.id is not None
        ],
    )

    groups: dict[str, list[PersonalValuePoolItem]] = {
        position: []
        for position in POOL_POSITIONS
    }

    for player_id, market_snapshot in market_snapshots_by_player_id.items():
        player = players.get(player_id)

        if player is None or player.position not in POOL_POSITIONS:
            continue

        underdog_position_rank = (
            underdog_by_player_id[
                player_id
            ].position_rank
            if player_id in underdog_by_player_id
            else None
        )
        saved_for_player = saved_by_player_id.get(
            player_id,
            [],
        )
        default_position_rank = _parse_position_rank(
            player.position,
            underdog_position_rank,
        )

        if (
            default_position_rank is None
            and not saved_for_player
        ):
            continue

        projection_context = _build_projection_context(
            position=player.position,
            age=calculate_age(player.birth_date),
            base_season=current_season,
            end_season=_get_projection_end_season(
                base_season=current_season,
                age=calculate_age(player.birth_date),
                position=player.position,
            ),
            default_position_rank=default_position_rank,
            saved_projections=saved_for_player,
            outcomes_by_projection_id=outcomes_by_projection_id,
            curve_rows_by_position=curve_rows_by_position,
        )
        player_payload = PersonalValuePlayer(
            player_id=player.player_id,
            name=player.full_name,
            position=player.position,
            team=player.team,
            age=calculate_age(player.birth_date),
            injury_status=player.injury_status,
            underdog_position_rank=underdog_position_rank,
            ktc_value=market_snapshot.ktc_value,
            fc_value=market_snapshot.fc_value,
            adp_value=market_snapshot.adp_value,
        )

        groups[player.position].append(
            PersonalValuePoolItem(
                player=player_payload,
                market_values=market_snapshot.metrics,
                custom_values=projection_context.custom_values,
                delta_values=_build_delta_values(
                    custom_values=projection_context.custom_values,
                    market_values=market_snapshot.metrics,
                ),
                is_customized=projection_context.is_customized,
            )
        )

    ordered_groups: list[PersonalValuePoolGroup] = []

    for position in POOL_POSITIONS:
        items = groups[position]

        if not items:
            continue

        items.sort(
            key=lambda item: item.player.name,
        )
        items.sort(
            key=lambda item: (
                item.custom_values.dynasty_roster_war
                if item.custom_values.dynasty_roster_war is not None
                else float("-inf")
            ),
            reverse=True,
        )
        ordered_groups.append(
            PersonalValuePoolGroup(
                position=position,
                players=items,
            )
        )

    return PersonalValuePoolResponse(
        context=PersonalValueLeagueContext(
            league_id=league.league_id,
            league_name=league.name,
            season=current_season,
            total_rosters=league.total_rosters,
        ),
        groups=ordered_groups,
    )


async def save_personal_value_detail(
    *,
    ctx: Context,
    league_id: str,
    player_id: str,
    payload: PersonalValueUpdateRequest,
) -> PersonalValueDetailResponse:
    _require_personal_values_context(
        ctx,
    )

    league = await _resolve_league_context(
        ctx=ctx,
        league_id=league_id,
    )
    player, underdog_position_rank = await _load_player_with_underdog_rank(
        ctx=ctx,
        player_id=player_id,
    )
    default_position_rank = _parse_position_rank(
        player.position,
        underdog_position_rank,
    )
    base_season = int(league.season)
    end_season = _get_projection_end_season(
        base_season=base_season,
        age=calculate_age(player.birth_date),
        position=player.position,
    )

    _validate_projection_update(
        base_season=base_season,
        end_season=end_season,
        payload=payload,
    )

    submitted_by_season = {
        item.season: item
        for item in payload.seasons
    }

    for season in range(
        base_season,
        end_season + 1,
    ):
        season_update = submitted_by_season.get(
            season,
        )

        if season_update is None:
            continue

        current_default_outcomes = (
            [(default_position_rank, 100.0)]
            if default_position_rank is not None
            else []
        )
        submitted_outcomes = [
            (
                outcome.position_rank,
                float(outcome.probability),
            )
            for outcome in season_update.outcomes
        ]
        is_customized = (
            submitted_outcomes != current_default_outcomes
        )

        await upsert_personal_projection(
            db=ctx.db,
            site_user_id=ctx.site_user.id,
            player_id=player_id,
            season=season,
            position=player.position,
            default_source="underdog",
            is_customized=is_customized,
            outcomes=submitted_outcomes,
        )

    return await get_personal_value_detail(
        ctx=ctx,
        league_id=league_id,
        player_id=player_id,
    )


def _outcome_pairs(outcomes) -> list[tuple[int, float]]:
    return [
        (outcome.position_rank, outcome.probability)
        for outcome in outcomes
    ]


def _ranked_outcomes(outcomes) -> list:
    """Outcome refs sorted by probability, highest first."""
    ranked = sorted(
        outcomes,
        key=lambda outcome: outcome.probability,
        reverse=True,
    )

    return [
        PersonalValueRankingOutcome(
            position_rank=outcome.position_rank,
            probability=outcome.probability,
        )
        for outcome in ranked
    ]


async def get_personal_value_rankings(
    *,
    ctx: Context,
    league_id: str,
    position: str,
    scope: str,
) -> PersonalValueRankingsResponse:
    """Position-wide personal ranking board data.

    scope="current" reads the current-season single outcome;
    scope="future" reads each player's default future trajectory (the
    first future season) and flags players whose later seasons
    diverge from it - those divergent years were individually edited
    and are never touched by board reordering.
    """
    _require_personal_values_context(ctx)

    league = await _resolve_league_context(
        ctx=ctx,
        league_id=league_id,
    )
    current_season = int(league.season)

    player_rows = await ctx.db.execute(
        select(Player).where(Player.position == position),
    )
    players = list(player_rows.scalars().all())
    player_ids = [p.player_id for p in players]

    saved = await get_personal_projections_for_site_user(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
        player_ids=player_ids,
    ) if player_ids else []

    outcomes_by_projection_id = await get_personal_projection_outcomes(
        db=ctx.db,
        projection_ids=[
            projection.id
            for projection in saved
            if projection.id is not None
        ],
    )

    saved_by_player_season: dict[
        tuple[str, int],
        tuple[list, bool],
    ] = {}

    for projection in saved:
        saved_by_player_season[
            (projection.player_id, projection.season)
        ] = (
            outcomes_by_projection_id.get(
                projection.id,
                [],
            ),
            projection.is_customized,
        )

    # Latest Underdog ADP row per player provides the fallback rank.
    underdog_rows = []
    if player_ids:
        underdog_result = await ctx.db.execute(
            select(UnderdogADP)
            .where(UnderdogADP.player_id.in_(player_ids))
            .order_by(desc(UnderdogADP.id)),
        )
        underdog_rows = list(
            underdog_result.scalars().all(),
        )

    default_rank_by_player: dict[str, int | None] = {}
    seen_player_ids: set[str] = set()
    for underdog_row in underdog_rows:
        if underdog_row.player_id in seen_player_ids:
            continue
        seen_player_ids.add(underdog_row.player_id)
        default_rank_by_player[underdog_row.player_id] = (
            _parse_position_rank(
                position,
                underdog_row.position_rank,
            )
        )

    entries: list[PersonalValueRankingEntry] = []

    for player in players:
        default_rank = default_rank_by_player.get(player.player_id)

        if scope == "current":
            outcomes, customized = saved_by_player_season.get(
                (player.player_id, current_season),
                ([], False),
            )
            ranked_outcomes = _ranked_outcomes(outcomes)
            primary = (
                ranked_outcomes[0].position_rank
                if ranked_outcomes
                else default_rank
            )
            secondary = (
                ranked_outcomes[1].position_rank
                if len(ranked_outcomes) > 1
                else None
            )
            divergent = False
        else:
            future_seasons = sorted(
                season
                for (pid, season) in saved_by_player_season
                if pid == player.player_id
                and season > current_season
            )

            if not future_seasons:
                primary = default_rank
                secondary = None
                ranked_outcomes = []
                customized = False
                divergent = False
            else:
                first_outcomes, first_customized = (
                    saved_by_player_season[
                        (player.player_id, future_seasons[0])
                    ]
                )
                ranked_outcomes = _ranked_outcomes(first_outcomes)
                primary = (
                    ranked_outcomes[0].position_rank
                    if ranked_outcomes
                    else default_rank
                )
                secondary = (
                    ranked_outcomes[1].position_rank
                    if len(ranked_outcomes) > 1
                    else None
                )
                customized = first_customized

                template_pairs = _outcome_pairs(first_outcomes)
                divergent = any(
                    _outcome_pairs(
                        saved_by_player_season[
                            (player.player_id, season)
                        ][0],
                    )
                    != template_pairs
                    for season in future_seasons[1:]
                )

        entries.append(
            PersonalValueRankingEntry(
                player_id=player.player_id,
                name=player.full_name,
                position=player.position or position,
                team=player.team,
                primary_rank=primary,
                outcomes=ranked_outcomes,
                secondary_rank=secondary,
                is_customized=customized,
                has_divergent_future_years=divergent,
            ),
        )

    entries.sort(
        key=lambda entry: (
            entry.primary_rank is None,
            entry.primary_rank if entry.primary_rank is not None else 0,
            entry.secondary_rank
            if entry.secondary_rank is not None
            else 10_000,
            entry.name,
        ),
    )

    return PersonalValueRankingsResponse(
        season=current_season,
        position=position,
        scope=scope,
        entries=entries,
    )


async def set_personal_value_rankings(
    *,
    ctx: Context,
    request: PersonalValueRankingsUpdateRequest,
) -> PersonalValueRankingsUpdateResponse:
    """Applies board reordering to personal projections.

    Current scope rewrites the current-season single outcome. Future
    scope rewrites every season that still matches the player's
    default future trajectory; individually-edited (divergent) seasons
    are deliberately left untouched.
    """
    _require_personal_values_context(ctx)

    if request.scope not in {"current", "future"}:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=422,
            detail="scope must be 'current' or 'future'.",
        )

    league = await _resolve_league_context(
        ctx=ctx,
        league_id=request.league_id,
    )
    current_season = int(league.season)

    updated = 0

    for entry in request.entries:
        player_row = await ctx.db.get(Player, entry.player_id)

        if player_row is None:
            continue

        age = calculate_age(player_row.birth_date)

        if request.scope == "current":
            await upsert_personal_projection(
                db=ctx.db,
                site_user_id=ctx.site_user.id,
                player_id=entry.player_id,
                season=current_season,
                position=player_row.position,
                default_source="underdog",
                is_customized=True,
                outcomes=[(entry.primary_rank, 100.0)],
            )
            updated += 1
            continue

        end_season = _get_projection_end_season(
            base_season=current_season,
            age=age,
            position=player_row.position,
        )

        saved = await get_personal_projections_for_player(
            db=ctx.db,
            site_user_id=ctx.site_user.id,
            player_id=entry.player_id,
        )
        future_saved = sorted(
            (
                projection
                for projection in saved
                if projection.season > current_season
            ),
            key=lambda projection: projection.season,
        )

        if future_saved:
            outcomes_by_id = await get_personal_projection_outcomes(
                db=ctx.db,
                projection_ids=[
                    projection.id
                    for projection in future_saved
                    if projection.id is not None
                ],
            )
            template_pairs = _outcome_pairs(
                outcomes_by_id.get(future_saved[0].id, []),
            )

            old_primary = (
                template_pairs[0][0] if template_pairs else None
            )
            spread = (
                template_pairs[1][0] - old_primary
                if len(template_pairs) > 1 and old_primary is not None
                else 0
            )

            # Tied template ranks (spread 0) keep both outcomes
            # equal rather than nulling the secondary rank.
            new_secondary = (
                entry.primary_rank + spread
                if len(template_pairs) > 1
                else None
            )

            for projection in future_saved:
                pairs = _outcome_pairs(
                    outcomes_by_id.get(projection.id, []),
                )

                if pairs != template_pairs:
                    # Individually edited year - hands off.
                    continue

                new_outcomes = [
                    (entry.primary_rank, pairs[0][1]),
                ]
                if len(pairs) > 1:
                    new_outcomes.append(
                        (new_secondary, pairs[1][1]),
                    )

                await upsert_personal_projection(
                    db=ctx.db,
                    site_user_id=ctx.site_user.id,
                    player_id=entry.player_id,
                    season=projection.season,
                    position=player_row.position,
                    default_source="underdog",
                    is_customized=True,
                    outcomes=new_outcomes,
                )
                updated += 1
        else:
            for season in range(
                current_season + 1,
                end_season + 1,
            ):
                await upsert_personal_projection(
                    db=ctx.db,
                    site_user_id=ctx.site_user.id,
                    player_id=entry.player_id,
                    season=season,
                    position=player_row.position,
                    default_source="underdog",
                    is_customized=True,
                    outcomes=[(entry.primary_rank, 100.0)],
                )
                updated += 1

    return PersonalValueRankingsUpdateResponse(updated=updated)


async def reset_personal_value_rankings(
    *,
    ctx: Context,
    request: PersonalValueRankingsResetRequest,
) -> PersonalValueRankingsResetResponse:
    """Strips personal customizations back to Underdog defaults.

    With player_id set, resets a single player across all seasons;
    otherwise resets every player at the given position.
    """
    _require_personal_values_context(ctx)

    await _resolve_league_context(
        ctx=ctx,
        league_id=request.league_id,
    )

    if request.player_id:
        player_ids = [request.player_id]
    elif request.position:
        rows = await ctx.db.execute(
            select(Player.player_id).where(
                Player.position == request.position,
            ),
        )
        player_ids = [
            row[0] for row in rows.all()
        ]
    else:
        rows = await ctx.db.execute(
            select(Player.player_id).where(
                Player.position.in_(DYNASTY_POSITIONS),
            ),
        )
        player_ids = [
            row[0] for row in rows.all()
        ]

    saved = await get_personal_projections_for_site_user(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
        player_ids=player_ids,
    ) if player_ids else []

    removed = await delete_personal_projections(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
        projection_ids=[
            projection.id
            for projection in saved
            if projection.id is not None
        ],
    )

    return PersonalValueRankingsResetResponse(
        reset_players=len(saved),
    )


async def sync_underdog_defaults(
    *,
    ctx: Context,
    league_id: str,
    position: str | None = None,
) -> PersonalValueRankingsResetResponse:
    """Freezes current Underdog ranks as personal values.

    Only touches players with NO stored projections (still on pure
    defaults); already-customized players are left alone. Writes one
    single-outcome projection per horizon season so later Underdog
    updates cannot move them.
    """
    _require_personal_values_context(ctx)

    league = await _resolve_league_context(
        ctx=ctx,
        league_id=league_id,
    )
    current_season = int(league.season)

    query = select(Player).where(
        Player.position == position,
    ) if position else select(Player).where(
        Player.position.in_(DYNASTY_POSITIONS),
    )
    players = list(
        (await ctx.db.execute(query)).scalars().all(),
    )

    if not players:
        return PersonalValueRankingsResetResponse(reset_players=0)

    player_ids = [p.player_id for p in players]
    saved = await get_personal_projections_for_site_user(
        db=ctx.db,
        site_user_id=ctx.site_user.id,
        player_ids=player_ids,
    )
    touched_ids = {projection.player_id for projection in saved}

    underdog_result = await ctx.db.execute(
        select(UnderdogADP)
        .where(UnderdogADP.player_id.in_(player_ids))
        .order_by(desc(UnderdogADP.id)),
    )
    raw_ud_rank_by_player: dict[str, str | None] = {}
    seen: set[str] = set()
    for underdog_row in underdog_result.scalars().all():
        if underdog_row.player_id in seen:
            continue
        seen.add(underdog_row.player_id)
        raw_ud_rank_by_player[underdog_row.player_id] = (
            underdog_row.position_rank
        )

    synced = 0

    for player in players:
        if player.player_id in touched_ids:
            continue

        default_rank = _parse_position_rank(
            player.position,
            raw_ud_rank_by_player.get(player.player_id),
        )
        if default_rank is None:
            continue

        end_season = _get_projection_end_season(
            base_season=current_season,
            age=calculate_age(player.birth_date),
            position=player.position,
        )

        for season in range(current_season, end_season + 1):
            await upsert_personal_projection(
                db=ctx.db,
                site_user_id=ctx.site_user.id,
                player_id=player.player_id,
                season=season,
                position=player.position,
                default_source="underdog",
                is_customized=False,
                outcomes=[(default_rank, 100.0)],
            )

        synced += 1

    return PersonalValueRankingsResetResponse(reset_players=synced)
