from __future__ import annotations

from app.models.db.sleeper.api import League, Roster


MIN_PROJECTABLE_WEEK = 4


def should_project_future_pick_slots(
    *,
    league: League,
    current_week: int,
) -> bool:
    return (
        league.is_dynasty
        and current_week >= MIN_PROJECTABLE_WEEK
        and league.status in {"in_season", "post_season"}
    )


def build_projected_slot_source_label(
    *,
    current_week: int,
) -> str:
    return (
        "Projected from current reverse-order standings "
        f"proxy through Week {current_week}"
    )


def build_projected_pick_slots_by_roster_id(
    *,
    league: League,
    rosters: list[Roster],
    current_week: int,
    projected_points_by_roster_id: dict[int, float] | None = None,
) -> dict[int, int]:
    if not should_project_future_pick_slots(
        league=league,
        current_week=current_week,
    ):
        return {}

    projected_points_by_roster_id = (
        projected_points_by_roster_id or {}
    )

    ordered_rosters = sorted(
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

    return {
        roster.roster_id: slot
        for slot, roster in enumerate(
            ordered_rosters,
            start=1,
        )
    }
