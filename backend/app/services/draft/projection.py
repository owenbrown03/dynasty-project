from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.models.db.sleeper.api import League, Roster


DRAFT_PICK_PROJECTION_METHODS = {
    "reverse_standings",
    "max_pf",
}
DEFAULT_DRAFT_PICK_PROJECTION_SETTINGS = {
    "enabled": True,
    "start_week": 4,
    "method": "max_pf",
}
MIN_DRAFT_PICK_PROJECTION_WEEK = 1
MAX_DRAFT_PICK_PROJECTION_WEEK = 18

DraftPickProjectionMethod = Literal[
    "reverse_standings",
    "max_pf",
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
    start_week = raw_settings.get(
        "start_week",
        DEFAULT_DRAFT_PICK_PROJECTION_SETTINGS["start_week"],
    )
    method = raw_settings.get(
        "method",
        DEFAULT_DRAFT_PICK_PROJECTION_SETTINGS["method"],
    )

    if not isinstance(enabled, bool):
        enabled = DEFAULT_DRAFT_PICK_PROJECTION_SETTINGS["enabled"]

    if not isinstance(start_week, int):
        start_week = DEFAULT_DRAFT_PICK_PROJECTION_SETTINGS["start_week"]

    start_week = max(
        MIN_DRAFT_PICK_PROJECTION_WEEK,
        min(MAX_DRAFT_PICK_PROJECTION_WEEK, start_week),
    )

    if method not in DRAFT_PICK_PROJECTION_METHODS:
        method = DEFAULT_DRAFT_PICK_PROJECTION_SETTINGS["method"]

    return {
        "enabled": enabled,
        "start_week": start_week,
        "method": method,
    }


def should_project_future_pick_slots(
    *,
    league: League,
    current_week: int,
    settings: dict[str, object] | None = None,
) -> bool:
    normalized = normalize_draft_pick_projection_settings(
        settings,
    )

    return (
        league.is_dynasty
        and normalized["enabled"] is True
        and current_week >= int(normalized["start_week"])
        and league.status in {"in_season", "post_season"}
    )


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
        or normalized["method"]
    )

    if resolved_method == "max_pf":
        label = (
            "Projected from reverse max PF through "
            f"Week {current_week}, using cumulative "
            "potential points first, then points for, "
            "then projected points as tiebreakers"
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
            f"{label}. Fell back from {fallback_from_method} "
            "because max PF data was unavailable."
        )

    return label


def build_draft_pick_projection_summary(
    *,
    settings: dict[str, object] | None,
) -> str:
    normalized = normalize_draft_pick_projection_settings(
        settings,
    )

    if normalized["enabled"] is not True:
        return "Projected pick slots are disabled."

    if normalized["method"] == "max_pf":
        method_label = "reverse max PF"
    else:
        method_label = "reverse standings proxy"

    return (
        "Projected future picks turn on in "
        f"Week {normalized['start_week']} using {method_label}."
    )


def _can_use_max_pf(
    rosters: list[Roster],
) -> bool:
    return any(roster.ppts > 0 for roster in rosters)


def _sort_rosters_by_standings_proxy(
    *,
    rosters: list[Roster],
    projected_points_by_roster_id: dict[int, float],
) -> list[Roster]:
    return sorted(
        rosters,
        key=lambda roster: (
            roster.wins,
            roster.losses + roster.ties,
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


def build_projected_pick_slots_by_roster_id(
    *,
    league: League,
    rosters: list[Roster],
    current_week: int,
    projected_points_by_roster_id: dict[int, float] | None = None,
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
    requested_method = normalized["method"]
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
    else:
        if requested_method == "max_pf":
            fallback_from_method = "max_pf"

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
