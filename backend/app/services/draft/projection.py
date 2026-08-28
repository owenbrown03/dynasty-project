from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal

from app.infrastructure.redis.client import RedisClient
from app.models.db.sleeper.api import League, Roster

DRAFT_PICK_PROJECTION_CACHE_TTL_SECONDS = (
    6 * 60 * 60
)
DRAFT_PICK_PROJECTION_CACHE_VERSION = "v2"

DRAFT_PICK_PROJECTION_METHODS = {
    "standings_proxy",
    "max_pf",
    "redraft_starter_war",
    "redraft_roster_war",
    "sleeper_projection",
    "ktc_redraft",
    "fantasycalc_redraft",
}
DRAFT_PICK_PROJECTION_PHASE_METHODS = {
    "none",
    *DRAFT_PICK_PROJECTION_METHODS,
}
DEFAULT_DRAFT_PICK_PROJECTION_SETTINGS = {
    "enabled": True,
    "switch_week": 4,
    "before_week_method": "none",
    "from_week_method": "sleeper_projection",
}
DEFAULT_FINANCE_PROJECTION_SETTINGS = {
    "same_as_draft_pick_projection": True,
    "settings": dict(
        DEFAULT_DRAFT_PICK_PROJECTION_SETTINGS,
    ),
}
MIN_DRAFT_PICK_PROJECTION_WEEK = 1
MAX_DRAFT_PICK_PROJECTION_WEEK = 18

DraftPickProjectionMethod = Literal[
    "standings_proxy",
    "max_pf",
    "redraft_starter_war",
    "redraft_roster_war",
    "sleeper_projection",
    "ktc_redraft",
    "fantasycalc_redraft",
]
DraftPickProjectionPhaseMethod = Literal[
    "none",
    "reverse_standings",
    "max_pf",
    "redraft_starter_war",
    "redraft_roster_war",
]


@dataclass
class DraftPickProjectionResult:
    slots_by_roster_id: dict[int, int]
    method_used: DraftPickProjectionMethod | None = None
    fallback_from_method: DraftPickProjectionMethod | None = None


def normalize_draft_pick_projection_settings(
    raw_settings: dict | None,
) -> dict[str, object]:
    raw_settings = raw_settings or {}

    enabled = raw_settings.get(
        "enabled",
        DEFAULT_DRAFT_PICK_PROJECTION_SETTINGS["enabled"],
    )

    # Backward compatibility for the earlier single-threshold model.
    switch_week = raw_settings.get(
        "switch_week",
        raw_settings.get(
            "start_week",
            DEFAULT_DRAFT_PICK_PROJECTION_SETTINGS["switch_week"],
        ),
    )
    before_week_method = raw_settings.get(
        "before_week_method",
        "none",
    )
    from_week_method = raw_settings.get(
        "from_week_method",
        raw_settings.get(
            "method",
            DEFAULT_DRAFT_PICK_PROJECTION_SETTINGS["from_week_method"],
        ),
    )

    if not isinstance(enabled, bool):
        enabled = DEFAULT_DRAFT_PICK_PROJECTION_SETTINGS["enabled"]

    if not isinstance(switch_week, int):
        switch_week = DEFAULT_DRAFT_PICK_PROJECTION_SETTINGS["switch_week"]

    switch_week = max(
        MIN_DRAFT_PICK_PROJECTION_WEEK,
        min(MAX_DRAFT_PICK_PROJECTION_WEEK, switch_week),
    )

    if before_week_method not in DRAFT_PICK_PROJECTION_PHASE_METHODS:
        before_week_method = DEFAULT_DRAFT_PICK_PROJECTION_SETTINGS["before_week_method"]

    if from_week_method not in DRAFT_PICK_PROJECTION_METHODS:
        from_week_method = DEFAULT_DRAFT_PICK_PROJECTION_SETTINGS["from_week_method"]

    return {
        "enabled": enabled,
        "switch_week": switch_week,
        "before_week_method": before_week_method,
        "from_week_method": from_week_method,
    }


def normalize_finance_projection_settings(
    raw_settings: dict | None,
) -> dict[str, object]:
    raw_settings = raw_settings or {}

    same_as_draft_pick_projection = raw_settings.get(
        "same_as_draft_pick_projection",
        raw_settings.get(
            "same_as_future_pick_projection",
            DEFAULT_FINANCE_PROJECTION_SETTINGS[
                "same_as_draft_pick_projection"
            ],
        ),
    )

    if not isinstance(
        same_as_draft_pick_projection,
        bool,
    ):
        same_as_draft_pick_projection = DEFAULT_FINANCE_PROJECTION_SETTINGS[
            "same_as_draft_pick_projection"
        ]

    return {
        "same_as_draft_pick_projection": (
            same_as_draft_pick_projection
        ),
        "settings": normalize_draft_pick_projection_settings(
            raw_settings.get("settings"),
        ),
    }


def resolve_finance_projection_settings(
    *,
    finance_settings: dict[str, object] | None,
    draft_pick_projection_settings: dict[str, object] | None,
    authenticated: bool,
) -> dict[str, object]:
    if not authenticated:
        return normalize_draft_pick_projection_settings(
            {
                "enabled": False,
                "switch_week": DEFAULT_DRAFT_PICK_PROJECTION_SETTINGS[
                    "switch_week"
                ],
                "before_week_method": "none",
                "from_week_method": DEFAULT_DRAFT_PICK_PROJECTION_SETTINGS[
                    "from_week_method"
                ],
            }
        )

    normalized_finance_settings = (
        normalize_finance_projection_settings(
            finance_settings,
        )
    )

    if normalized_finance_settings[
        "same_as_draft_pick_projection"
    ]:
        return normalize_draft_pick_projection_settings(
            draft_pick_projection_settings,
        )

    return normalize_draft_pick_projection_settings(
        normalized_finance_settings["settings"],
    )


def resolve_draft_pick_projection_method(
    *,
    current_week: int,
    settings: dict[str, object] | None,
) -> DraftPickProjectionPhaseMethod:
    normalized = normalize_draft_pick_projection_settings(
        settings,
    )

    if current_week < int(normalized["switch_week"]):
        return normalized["before_week_method"]  # type: ignore[return-value]

    return normalized["from_week_method"]  # type: ignore[return-value]


def should_project_future_pick_slots(
    *,
    league: League,
    current_week: int,
    settings: dict[str, object] | None = None,
) -> bool:
    normalized = normalize_draft_pick_projection_settings(
        settings,
    )
    active_method = resolve_draft_pick_projection_method(
        current_week=current_week,
        settings=normalized,
    )

    return (
        league.is_dynasty
        and normalized["enabled"] is True
        and active_method != "none"
        and league.status in {"in_season", "post_season"}
    )


def _format_method_label(
    method: DraftPickProjectionMethod,
) -> str:
    if method == "max_pf":
        return "reverse max PF"
    if method == "redraft_starter_war":
        return "redraft starter WAR"
    if method == "redraft_roster_war":
        return "redraft roster WAR"
    if method == "sleeper_projection":
        return "sleeper projected points"
    if method == "ktc_redraft":
        return "KTC (redraft)"
    if method == "fantasycalc_redraft":
        return "FantasyCalc (redraft)"
    return "standings proxy"


def build_projected_slot_source_label(
    *,
    current_week: int,
    settings: dict[str, object] | None = None,
    method_used: DraftPickProjectionMethod | None = None,
    fallback_from_method: DraftPickProjectionMethod | None = None,
) -> str:
    normalized = normalize_draft_pick_projection_settings(
        settings,
    )
    resolved_method = (
        method_used
        or normalized["from_week_method"]
    )

    if resolved_method == "max_pf":
        label = (
            "Projected from max PF through "
            f"Week {current_week}, using cumulative "
            "potential points first, then points for, "
            "then projected points as tiebreakers"
        )
    elif resolved_method == "redraft_starter_war":
        label = (
            "Projected from redraft starter WAR, using lower "
            "starter WAR first, then points for, then projected "
            "points as tiebreakers"
        )
    elif resolved_method == "redraft_roster_war":
        label = (
            "Projected from redraft roster WAR, using lower "
            "roster WAR first, then points for, then projected "
            "points as tiebreakers"
        )
    elif resolved_method == "sleeper_projection":
        label = (
            "Projected from sleeper projected points, using "
            "lower total projection first, then points for, then "
            "projected points as tiebreakers"
        )
    elif resolved_method == "ktc_redraft":
        label = (
            "Projected from KTC redraft values, using lower total "
            "value first, then points for, then projected points "
            "as tiebreakers"
        )
    elif resolved_method == "fantasycalc_redraft":
        label = (
            "Projected from FantasyCalc redraft values, using "
            "lower total value first, then points for, then "
            "projected points as tiebreakers"
        )
    else:
        label = (
            "Projected from the standings proxy "
            f"through Week {current_week}, using record "
            "first, then points for, then projected points as "
            "tiebreakers"
        )

    if (
        fallback_from_method is not None
        and fallback_from_method != resolved_method
    ):
        return (
            f"{label}. Fell back from "
            f"{_format_method_label(fallback_from_method)} "
            "because that data was unavailable."
        )

    return label


def build_draft_pick_projection_summary(
    *,
    current_week: int,
    settings: dict[str, object] | None,
    method_used: DraftPickProjectionMethod | None = None,
    fallback_from_method: DraftPickProjectionMethod | None = None,
) -> str | None:
    normalized = normalize_draft_pick_projection_settings(
        settings,
    )

    if normalized["enabled"] is not True:
        return None

    active_method = resolve_draft_pick_projection_method(
        current_week=current_week,
        settings=normalized,
    )

    if active_method == "none":
        return None

    summary = build_projected_slot_source_label(
        current_week=current_week,
        settings=normalized,
        method_used=method_used,
        fallback_from_method=fallback_from_method,
    )

    if normalized["before_week_method"] == "none":
        return (
            f"Projection starts in Week {normalized['switch_week']}. "
            f"{summary}"
        )

    if current_week < int(normalized["switch_week"]):
        return (
            f"Using {_format_method_label(active_method)} before Week "
            f"{normalized['switch_week']}. {summary}"
        )

    return (
        f"Using {_format_method_label(active_method)} from Week "
        f"{normalized['switch_week']} onward. {summary}"
    )


def _can_use_max_pf(
    rosters: list[Roster],
) -> bool:
    return any(roster.ppts > 0 for roster in rosters)


def _has_metric_values(
    values_by_roster_id: dict[int, float] | None,
) -> bool:
    if not values_by_roster_id:
        return False

    return any(abs(value) > 0 for value in values_by_roster_id.values())


def _sort_rosters_by_standings_proxy(
    *,
    rosters: list[Roster],
    projected_points_by_roster_id: dict[int, float],
) -> list[Roster]:
    return sorted(
        rosters,
        key=lambda roster: (
            roster.wins,
            -(roster.losses + roster.ties),
            roster.fpts,
            projected_points_by_roster_id.get(
                roster.roster_id,
                0.0,
            ),
            roster.roster_id,
        ),
    )


def _sort_rosters_by_max_pf(
    *,
    rosters: list[Roster],
    projected_points_by_roster_id: dict[int, float],
) -> list[Roster]:
    return sorted(
        rosters,
        key=lambda roster: (
            roster.ppts,
            roster.fpts,
            projected_points_by_roster_id.get(
                roster.roster_id,
                0.0,
            ),
            roster.roster_id,
        ),
    )


def _sort_rosters_by_metric(
    *,
    rosters: list[Roster],
    projected_points_by_roster_id: dict[int, float],
    values_by_roster_id: dict[int, float],
) -> list[Roster]:
    return sorted(
        rosters,
        key=lambda roster: (
            values_by_roster_id.get(
                roster.roster_id,
                0.0,
            ),
            roster.fpts,
            projected_points_by_roster_id.get(
                roster.roster_id,
                0.0,
            ),
            roster.roster_id,
        ),
    )


def _build_draft_pick_projection_cache_key(
    *,
    league: League,
    rosters: list[Roster],
    current_week: int,
    projected_points_by_roster_id: dict[int, float] | None,
    redraft_starter_war_by_roster_id: dict[int, float] | None,
    redraft_roster_war_by_roster_id: dict[int, float] | None,
    redraft_value_by_roster_id: dict[int, float] | None = None,
    settings: dict[str, object] | None = None,
) -> str:
    digest = hashlib.sha256()
    digest.update(
        json.dumps(
            {
                "league": {
                    "league_id": league.league_id,
                    "season": league.season,
                    "status": league.status,
                    "total_rosters": league.total_rosters,
                    "is_dynasty": league.is_dynasty,
                },
                "current_week": current_week,
                "settings": normalize_draft_pick_projection_settings(
                    settings,
                ),
                "rosters": [
                    {
                        "roster_id": roster.roster_id,
                        "wins": roster.wins,
                        "losses": roster.losses,
                        "ties": roster.ties,
                        "fpts": roster.fpts,
                        "ppts": roster.ppts,
                    }
                    for roster in sorted(
                        rosters,
                        key=lambda roster: roster.roster_id,
                    )
                ],
                "projected_points_by_roster_id": (
                    projected_points_by_roster_id
                    or {}
                ),
                "redraft_starter_war_by_roster_id": (
                    redraft_starter_war_by_roster_id
                    or {}
                ),
                "redraft_roster_war_by_roster_id": (
                    redraft_roster_war_by_roster_id
                    or {}
                ),
                "redraft_value_by_roster_id": (
                    redraft_value_by_roster_id or {}
                ),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    return (
        "draft-pick-projection:"
        f"{DRAFT_PICK_PROJECTION_CACHE_VERSION}:"
        f"{digest.hexdigest()}"
    )


def build_projected_pick_slots_by_roster_id(
    *,
    league: League,
    rosters: list[Roster],
    current_week: int,
    projected_points_by_roster_id: dict[int, float] | None = None,
    redraft_starter_war_by_roster_id: dict[int, float] | None = None,
    redraft_roster_war_by_roster_id: dict[int, float] | None = None,
    redraft_value_by_roster_id: dict[int, float] | None = None,
    settings: dict[str, object] | None = None,
) -> DraftPickProjectionResult:
    normalized = normalize_draft_pick_projection_settings(
        settings,
    )
    if not should_project_future_pick_slots(
        league=league,
        current_week=current_week,
        settings=normalized,
    ):
        return DraftPickProjectionResult(
            slots_by_roster_id={},
        )

    projected_points_by_roster_id = (
        projected_points_by_roster_id or {}
    )
    requested_method = resolve_draft_pick_projection_method(
        current_week=current_week,
        settings=normalized,
    )
    method_used: DraftPickProjectionMethod = "reverse_standings"
    fallback_from_method: DraftPickProjectionMethod | None = None

    if (
        requested_method == "max_pf"
        and _can_use_max_pf(rosters)
    ):
        ordered_rosters = _sort_rosters_by_max_pf(
            rosters=rosters,
            projected_points_by_roster_id=(
                projected_points_by_roster_id
            ),
        )
        method_used = "max_pf"
    elif (
        requested_method == "redraft_starter_war"
        and _has_metric_values(redraft_starter_war_by_roster_id)
    ):
        ordered_rosters = _sort_rosters_by_metric(
            rosters=rosters,
            projected_points_by_roster_id=(
                projected_points_by_roster_id
            ),
            values_by_roster_id=(
                redraft_starter_war_by_roster_id or {}
            ),
        )
        method_used = "redraft_starter_war"
    elif (
        requested_method == "redraft_roster_war"
        and _has_metric_values(redraft_roster_war_by_roster_id)
    ):
        ordered_rosters = _sort_rosters_by_metric(
            rosters=rosters,
            projected_points_by_roster_id=(
                projected_points_by_roster_id
            ),
            values_by_roster_id=(
                redraft_roster_war_by_roster_id or {}
            ),
        )
        method_used = "redraft_roster_war"
    elif (
        requested_method in REDRAFT_MARKET_METHODS
        and _has_metric_values(redraft_value_by_roster_id)
    ):
        ordered_rosters = _sort_rosters_by_metric(
            rosters=rosters,
            projected_points_by_roster_id=(
                projected_points_by_roster_id
            ),
            values_by_roster_id=(
                redraft_value_by_roster_id or {}
            ),
        )
        method_used = requested_method
    else:
        if requested_method != "reverse_standings":
            fallback_from_method = requested_method

        ordered_rosters = _sort_rosters_by_standings_proxy(
            rosters=rosters,
            projected_points_by_roster_id=(
                projected_points_by_roster_id
            ),
        )

    return DraftPickProjectionResult(
        slots_by_roster_id={
            roster.roster_id: slot
            for slot, roster in enumerate(
                ordered_rosters,
                start=1,
            )
        },
        method_used=method_used,
        fallback_from_method=fallback_from_method,
    )


async def build_cached_projected_pick_slots_by_roster_id(
    *,
    redis: RedisClient | None,
    league: League,
    rosters: list[Roster],
    current_week: int,
    projected_points_by_roster_id: dict[int, float] | None = None,
    redraft_starter_war_by_roster_id: dict[int, float] | None = None,
    redraft_roster_war_by_roster_id: dict[int, float] | None = None,
    redraft_value_by_roster_id: dict[int, float] | None = None,
    settings: dict[str, object] | None = None,
) -> DraftPickProjectionResult:
    cache_key = _build_draft_pick_projection_cache_key(
        league=league,
        rosters=rosters,
        current_week=current_week,
        projected_points_by_roster_id=(
            projected_points_by_roster_id
        ),
        redraft_starter_war_by_roster_id=(
            redraft_starter_war_by_roster_id
        ),
        redraft_roster_war_by_roster_id=(
            redraft_roster_war_by_roster_id
        ),
        redraft_value_by_roster_id=(
            redraft_value_by_roster_id
        ),
        settings=settings,
    )

    if redis is not None:
        cached_payload = await redis.get(
            cache_key,
        )

        if cached_payload:
            cached_result = json.loads(cached_payload)
            cached_slots = cached_result.get(
                "slots_by_roster_id",
                {},
            )

            return DraftPickProjectionResult(
                slots_by_roster_id={
                    int(roster_id): int(slot)
                    for roster_id, slot in cached_slots.items()
                },
                method_used=cached_result.get(
                    "method_used",
                ),
                fallback_from_method=cached_result.get(
                    "fallback_from_method",
                ),
            )

    result = build_projected_pick_slots_by_roster_id(
        league=league,
        rosters=rosters,
        current_week=current_week,
        projected_points_by_roster_id=(
            projected_points_by_roster_id
        ),
        redraft_starter_war_by_roster_id=(
            redraft_starter_war_by_roster_id
        ),
        redraft_roster_war_by_roster_id=(
            redraft_roster_war_by_roster_id
        ),
        redraft_value_by_roster_id=(
            redraft_value_by_roster_id
        ),
        settings=settings,
    )

    if redis is not None:
        await redis.set(
            cache_key,
            json.dumps(
                {
                    "slots_by_roster_id": (
                        result.slots_by_roster_id
                    ),
                    "method_used": result.method_used,
                    "fallback_from_method": (
                        result.fallback_from_method
                    ),
                },
                separators=(",", ":"),
            ),
            ttl_seconds=(
                DRAFT_PICK_PROJECTION_CACHE_TTL_SECONDS
            ),
        )

    return result


async def build_redraft_value_by_roster_id(
    db,
    rosters: list[Roster],
    basis: str = "ktc",
) -> dict[int, float]:
    """Total redraft market value per roster.

    Backs the redraft_value_system projection method and the advisor
    contention bands: both project redraft finish from the market
    system chosen in settings (#165 phase 3).
    """
    from app.crud.value import get_player_values

    player_ids = {
        player_id
        for roster in rosters
        for player_id in (roster.players or [])
    }

    if not player_ids:
        return {}

    values = await get_player_values(
        db,
        player_ids=list(player_ids),
        redraft_war_players=[],
        value_context="redraft",
    )

    def _basis_value(value) -> float:
        if basis == "fantasycalc":
            return value.fc_value or 0.0
        if basis == "sleeper_projection":
            return value.projected_points or 0.0
        if basis == "redraft_roster_war":
            return value.redraft_roster_war or 0.0
        if basis == "redraft_starter_war":
            return value.redraft_starter_war or 0.0
        if basis == "dynasty_roster_war":
            return value.dynasty_roster_war or 0.0
        if basis == "dynasty_starter_war":
            return value.dynasty_starter_war or 0.0
        # my_war / sleeper_war parameterized configs default to the
        # dynasty roster WAR leg.
        if basis in {"my_war", "sleeper_war"}:
            return value.dynasty_roster_war or 0.0
        if basis == "adp":
            return value.adp_value or 0.0
        return value.ktc_value or 0.0

    value_by_player = {
        value.player_id: _basis_value(value)
        for value in values
    }

    return {
        roster.roster_id: round(
            sum(
                value_by_player.get(player_id, 0.0)
                for player_id in (roster.players or [])
            ),
            2,
        )
        for roster in rosters
    }


# Methods that rank rosters by a redraft market-source sum; each
# maps to the basis build_redraft_value_by_roster_id should sum.
REDRAFT_MARKET_METHODS = {
    "sleeper_projection",
    "ktc_redraft",
    "fantasycalc_redraft",
}


def redraft_projection_basis_for_method(
    method: str,
) -> str | None:
    if method == "sleeper_projection":
        return "sleeper_projection"
    if method == "ktc_redraft":
        return "ktc"
    if method == "fantasycalc_redraft":
        return "fantasycalc"
    return None


def redraft_value_system_active(
    *,
    current_week: int,
    settings: dict[str, object] | None,
) -> bool:
    """Whether the active phase method ranks by a redraft market
    source.

    Callers use this to skip fetching redraft market sums when another
    method is active.
    """
    return (
        resolve_draft_pick_projection_method(
            current_week=current_week,
            settings=settings,
        )
        in REDRAFT_MARKET_METHODS
    )
