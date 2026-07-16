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
DRAFT_PICK_PROJECTION_CACHE_VERSION = "v1"

DRAFT_PICK_PROJECTION_METHODS = {
    "reverse_standings",
    "max_pf",
    "redraft_starter_war",
    "redraft_roster_war",
}
DRAFT_PICK_PROJECTION_PHASE_METHODS = {
    "none",
    *DRAFT_PICK_PROJECTION_METHODS,
}
DEFAULT_DRAFT_PICK_PROJECTION_SETTINGS = {
    "enabled": True,
    "switch_week": 4,
    "before_week_method": "none",
    "from_week_method": "max_pf",
}
MIN_DRAFT_PICK_PROJECTION_WEEK = 1
MAX_DRAFT_PICK_PROJECTION_WEEK = 18

DraftPickProjectionMethod = Literal[
    "reverse_standings",
    "max_pf",
    "redraft_starter_war",
    "redraft_roster_war",
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
    return "reverse standings proxy"


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
            "Projected from reverse max PF through "
            f"Week {current_week}, using cumulative "
            "potential points first, then points for, "
            "then projected points as tiebreakers"
        )
    elif resolved_method == "redraft_starter_war":
        label = (
            "Projected from reverse redraft starter WAR "
            f"through Week {current_week}, using lower starter "
            "WAR first, then points for, then projected points "
            "as tiebreakers"
        )
    elif resolved_method == "redraft_roster_war":
        label = (
            "Projected from reverse redraft roster WAR "
            f"through Week {current_week}, using lower roster "
            "WAR first, then points for, then projected points "
            "as tiebreakers"
        )
    else:
        label = (
            "Projected from the current reverse-order standings "
            f"proxy through Week {current_week}, using record "
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
    settings: dict[str, object] | None,
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
