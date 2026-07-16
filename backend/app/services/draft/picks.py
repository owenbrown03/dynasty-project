from __future__ import annotations

from collections import defaultdict

from app.models.db.sleeper.api import Draft, League, Roster, User
from app.schemas.draft import DraftPickAsset
from app.services.draft.values import ResolvedPickValue


def build_pick_label(
    *,
    season: str,
    round_number: int,
    og_roster_id: int,
    current_owner_roster_id: int,
    roster_name_by_id: dict[int, str],
    slot: int | None = None,
    projected_slot: int | None = None,
    is_projected: bool = False,
) -> str:
    resolved_slot = (
        slot
        if slot is not None
        else projected_slot
    )

    suffix = " (proj.)" if is_projected else ""

    if resolved_slot is not None:
        base = (
            f"{season} Pick {round_number}.{resolved_slot:02d}"
            f"{suffix}"
        )
    else:
        base = f"{season} Round {round_number}"

    if og_roster_id == current_owner_roster_id:
        return base

    original_owner_name = roster_name_by_id.get(
        og_roster_id,
        f"Roster {og_roster_id}",
    )

    return f"{base} (from {original_owner_name})"


def get_first_future_pick_season(
    league: League,
    *,
    drafts: list[Draft] | None = None,
    completed_draft_seasons: set[str] | None = None,
) -> str:
    current_season = int(league.season)
    current_season_str = str(current_season)
    completed_draft_seasons = completed_draft_seasons or set()
    drafts = drafts or []

    if current_season_str in completed_draft_seasons:
        return str(current_season + 1)

    if any(
        str(draft.season) == current_season_str
        for draft in drafts
    ):
        return current_season_str

    if league.status in {
        "in_season",
        "post_season",
        "complete",
    }:
        return str(current_season + 1)

    return str(current_season)


def build_roster_name_by_id(
    *,
    rosters: list[Roster],
    users_by_id: dict[str, User],
) -> dict[int, str]:
    output: dict[int, str] = {}

    for roster in rosters:
        if roster.owner_id and roster.owner_id in users_by_id:
            output[roster.roster_id] = users_by_id[
                roster.owner_id
            ].display_name
        else:
            output[roster.roster_id] = (
                f"Team {roster.roster_id}"
            )

    return output


def get_league_draft_for_season(
    *,
    drafts: list[Draft],
    season: str,
) -> Draft | None:
    for draft in drafts:
        if str(draft.season) == str(season):
            return draft

    return None


def build_slot_by_roster_id(
    *,
    draft: Draft | None,
    rosters: list[Roster],
) -> dict[int, int]:
    if draft is None:
        return {}

    if draft.slot_to_roster_id:
        return {
            int(roster_id): int(slot)
            for slot, roster_id in draft.slot_to_roster_id.items()
            if roster_id is not None
        }

    if not draft.draft_order:
        return {}

    owner_id_by_roster_id = {
        roster.roster_id: roster.owner_id
        for roster in rosters
        if roster.owner_id
    }

    slot_by_roster_id: dict[int, int] = {}

    for roster_id, owner_id in owner_id_by_roster_id.items():
        slot = draft.draft_order.get(owner_id)

        if slot is not None:
            slot_by_roster_id[roster_id] = int(slot)

    return slot_by_roster_id


def build_owned_pick_assets_by_roster_id(
    *,
    league: League,
    rosters: list[Roster],
    drafts: list[Draft],
    traded_picks: list[tuple[object, int]],
    roster_name_by_id: dict[int, str],
    seasons_ahead: int = 3,
    resolved_values_by_pick_key: dict[
        tuple[str, int, int],
        ResolvedPickValue,
    ] | None = None,
    projected_slots_by_season_and_roster_id: dict[
        tuple[str, int],
        int,
    ] | None = None,
    projected_slot_source_label: str | None = None,
    completed_draft_seasons: set[str] | None = None,
) -> dict[int, list[DraftPickAsset]]:
    output: dict[int, list[DraftPickAsset]] = defaultdict(list)
    resolved_values_by_pick_key = resolved_values_by_pick_key or {}
    projected_slots_by_season_and_roster_id = (
        projected_slots_by_season_and_roster_id
        or {}
    )

    start_season = int(
        get_first_future_pick_season(
            league,
            drafts=drafts,
            completed_draft_seasons=completed_draft_seasons,
        )
    )
    seasons = [
        str(start_season + offset)
        for offset in range(seasons_ahead)
    ]

    draft_rounds = int(
        league.settings.get(
            "draft_rounds",
            4,
        )
    )
    current_league_season = str(start_season)
    next_league_season = str(start_season + 1)

    owner_by_pick_key: dict[
        tuple[str, int, int],
        int,
    ] = {
        (
            season,
            round_number,
            roster.roster_id,
        ): roster.roster_id
        for season in seasons
        for round_number in range(1, draft_rounds + 1)
        for roster in rosters
    }

    for traded_pick, _ in traded_picks:
        pick_key = (
            str(traded_pick.season),
            int(traded_pick.round),
            int(traded_pick.og_roster_id),
        )

        if pick_key not in owner_by_pick_key:
            continue

        owner_by_pick_key[pick_key] = int(
            traded_pick.new_roster_id,
        )

    slot_maps_by_season = {
        season: build_slot_by_roster_id(
            draft=get_league_draft_for_season(
                drafts=drafts,
                season=season,
            ),
            rosters=rosters,
        )
        for season in seasons
    }

    for (
        season,
        round_number,
        og_roster_id,
    ), current_owner_roster_id in owner_by_pick_key.items():
        slot = slot_maps_by_season.get(
            season,
            {},
        ).get(og_roster_id)
        projected_slot = None
        should_show_slot = season in {
            current_league_season,
            next_league_season,
        }

        if not should_show_slot:
            slot = None

        if should_show_slot and slot is None:
            projected_slot = (
                projected_slots_by_season_and_roster_id.get(
                    (
                        season,
                        og_roster_id,
                    )
                )
            )

        is_projected = (
            slot is None
            and projected_slot is not None
        )

        output[current_owner_roster_id].append(
            DraftPickAsset(
                season=season,
                round=round_number,
                og_roster_id=og_roster_id,
                current_owner_roster_id=current_owner_roster_id,
                original_owner_name=roster_name_by_id.get(
                    og_roster_id,
                ),
                current_owner_name=roster_name_by_id.get(
                    current_owner_roster_id,
                ),
                slot=slot,
                projected_slot=projected_slot,
                slot_source_label=(
                    projected_slot_source_label
                    if is_projected
                    and should_show_slot
                    else None
                ),
                label=build_pick_label(
                    season=season,
                    round_number=round_number,
                    og_roster_id=og_roster_id,
                    current_owner_roster_id=current_owner_roster_id,
                    roster_name_by_id=roster_name_by_id,
                    slot=slot,
                    projected_slot=projected_slot,
                    is_projected=is_projected,
                ),
                selected_value=resolved_values_by_pick_key.get(
                    (
                        season,
                        round_number,
                        og_roster_id,
                    ),
                ).value if (
                    season,
                    round_number,
                    og_roster_id,
                ) in resolved_values_by_pick_key else None,
                value_source_label=resolved_values_by_pick_key.get(
                    (
                        season,
                        round_number,
                        og_roster_id,
                    ),
                ).source_label if (
                    season,
                    round_number,
                    og_roster_id,
                ) in resolved_values_by_pick_key else None,
            )
        )

    for roster_id, picks in output.items():
        picks.sort(
            key=lambda pick: (
                int(pick.season),
                pick.round,
                (
                    pick.slot
                    if pick.slot is not None
                    else (
                        pick.projected_slot
                        if pick.projected_slot is not None
                        else 999
                    )
                ),
                pick.og_roster_id,
            ),
        )

    return dict(output)
