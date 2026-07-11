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
) -> str:
    if slot is not None:
        return f"{season} Pick {round_number}.{slot:02d}"

    original_owner_name = roster_name_by_id.get(
        og_roster_id,
        f"Roster {og_roster_id}",
    )

    if og_roster_id == current_owner_roster_id:
        return (
            f"{season} Round {round_number} "
            f"({original_owner_name}'s original)"
        )

    return (
        f"{season} Round {round_number} "
        f"(from {original_owner_name})"
    )


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

    return drafts[0] if drafts else None


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
) -> dict[int, list[DraftPickAsset]]:
    output: dict[int, list[DraftPickAsset]] = defaultdict(list)
    resolved_values_by_pick_key = resolved_values_by_pick_key or {}

    start_season = int(league.season)
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
                label=build_pick_label(
                    season=season,
                    round_number=round_number,
                    og_roster_id=og_roster_id,
                    current_owner_roster_id=current_owner_roster_id,
                    roster_name_by_id=roster_name_by_id,
                    slot=slot,
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
                pick.slot if pick.slot is not None else 999,
                pick.og_roster_id,
            ),
        )

    return dict(output)
