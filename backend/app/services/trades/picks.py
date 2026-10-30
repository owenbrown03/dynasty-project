from __future__ import annotations

import asyncio
import logging

from app.schemas.trades import TradeDraftPickAsset


logger = logging.getLogger(__name__)


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
    """
    Build a human-readable label for one specific original draft pick.

    Example:
        2027 Pick 1.04 (proj.) (browntown333's original)
        2027 Pick 1.09 (proj.) (from Darven)
        2028 Round 1 (browntown333's original)
    """

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

    original_owner_name = roster_name_by_id.get(
        og_roster_id,
        f"Roster {og_roster_id}",
    )

    if og_roster_id == current_owner_roster_id:
        return (
            f"{base} "
            f"({original_owner_name}'s original)"
        )

    return (
        f"{base} "
        f"(from {original_owner_name})"
    )


async def get_current_pick_assets_by_league(
    *,
    sleeper,
    rosters_by_league_id: dict[str, list],
    requested_picks: list[tuple[str, int]],
    roster_names_by_league_id: dict[str, dict[int, str]],
    slots_by_league: dict[str, dict[tuple[str, int], int]] | None = None,
    projected_slots_by_league: dict[str, dict[tuple[str, int], int]] | None = None,
) -> dict[str, list[TradeDraftPickAsset]]:
    """
    Resolve current ownership of one or more pick year/round pairs across leagues.

    Source of truth:
        Sleeper's /league/{league_id}/traded_picks endpoint.

    Baseline:
        Every roster owns its own original pick.

    Override:
        For every matching Sleeper traded-pick row:
            roster_id = original owner
            owner_id = current owner

    This correctly handles trades from before this app started syncing.
    """

    league_ids = list(
        rosters_by_league_id.keys(),
    )

    if not league_ids:
        return {}

    requested_pick_set = {
        (
            str(season),
            int(round_number),
        )
        for season, round_number in requested_picks
    }

    # Start from the normal baseline:
    #
    # {
    #   league_id: {
    #       (original_roster_id, "2027", 2): current_owner_roster_id
    #   }
    # }
    pick_owner_by_league: dict[
        str,
        dict[tuple[int, str, int], int],
    ] = {}

    for league_id, rosters in rosters_by_league_id.items():
        pick_owner_by_league[league_id] = {
            (
                roster.roster_id,
                str(season),
                int(round_number),
            ): roster.roster_id
            for roster in rosters
            for season, round_number in requested_picks
        }

    # One current-pick-state request per league, concurrently.
    traded_pick_results = await asyncio.gather(
        *[
            sleeper.read.get_traded_picks(
                league_id,
            )
            for league_id in league_ids
        ],
        return_exceptions=True,
    )

    # Apply Sleeper's current ownership overrides.
    for league_id, traded_picks in zip(
        league_ids,
        traded_pick_results,
    ):
        if isinstance(
            traded_picks,
            Exception,
        ):
            logger.error(
                "Unable to fetch current traded picks "
                "league=%s error=%s",
                league_id,
                traded_picks,
            )

            # Do not claim that picks are tradable when we could not verify
            # current ownership. Returning no assets makes that league
            # unavailable for this requested pick.
            pick_owner_by_league[league_id] = {}
            continue

        league_pick_owners = pick_owner_by_league[
            league_id
        ]

        for traded_pick in traded_picks:
            requested_key = (
                str(traded_pick.season),
                int(traded_pick.round),
            )

            if requested_key not in requested_pick_set:
                continue

            if (
                traded_pick.roster_id is None
                or traded_pick.owner_id is None
            ):
                logger.warning(
                    "Ignoring incomplete Sleeper traded pick "
                    "league=%s season=%s round=%s "
                    "roster_id=%s owner_id=%s",
                    league_id,
                    traded_pick.season,
                    traded_pick.round,
                    traded_pick.roster_id,
                    traded_pick.owner_id,
                )
                continue

            pick_key = (
                int(traded_pick.roster_id),
                str(traded_pick.season),
                int(traded_pick.round),
            )

            # A pick can only be overridden if its original roster still
            # exists in our current local roster list.
            if pick_key not in league_pick_owners:
                logger.warning(
                    "Sleeper traded pick referenced unknown "
                    "original roster league=%s pick=%s",
                    league_id,
                    pick_key,
                )
                continue

            league_pick_owners[pick_key] = int(
                traded_pick.owner_id,
            )

    assets_by_league_id: dict[
        str,
        list[TradeDraftPickAsset],
    ] = {}

    for league_id, pick_owner_by_key in (
        pick_owner_by_league.items()
    ):
        roster_name_by_id = (
            roster_names_by_league_id.get(
                league_id,
                {},
            )
        )

        assets: list[TradeDraftPickAsset] = []

        league_slots = (slots_by_league or {}).get(league_id, {})
        league_projected_slots = (projected_slots_by_league or {}).get(league_id, {})

        for (
            og_roster_id,
            season,
            round_number,
        ), current_owner_roster_id in (
            pick_owner_by_key.items()
        ):
            slot = league_slots.get((season, og_roster_id))
            projected_slot = None
            if slot is None:
                projected_slot = league_projected_slots.get((season, og_roster_id))
            is_projected = slot is None and projected_slot is not None

            assets.append(
                TradeDraftPickAsset(
                    season=season,
                    round=round_number,
                    og_roster_id=og_roster_id,
                    current_owner_roster_id=(
                        current_owner_roster_id
                    ),
                    original_owner_name=(
                        roster_name_by_id.get(
                            og_roster_id,
                        )
                    ),
                    slot=slot,
                    projected_slot=projected_slot,
                    label=build_pick_label(
                        season=season,
                        round_number=round_number,
                        og_roster_id=og_roster_id,
                        current_owner_roster_id=(
                            current_owner_roster_id
                        ),
                        roster_name_by_id=(
                            roster_name_by_id
                        ),
                        slot=slot,
                        projected_slot=projected_slot,
                        is_projected=is_projected,
                    ),
                )
            )

        assets_by_league_id[league_id] = sorted(
            assets,
            key=lambda asset: (
                asset.current_owner_roster_id,
                asset.slot or asset.projected_slot or 999,
                asset.og_roster_id,
            ),
        )

    return assets_by_league_id


def get_owned_matching_picks(
    *,
    pick_assets: list[TradeDraftPickAsset],
    owner_roster_id: int,
) -> list[TradeDraftPickAsset]:
    """
    Return only picks currently owned by this roster.
    """

    return [
        pick
        for pick in pick_assets
        if (
            pick.current_owner_roster_id
            == owner_roster_id
        )
    ]


def build_sleeper_draft_pick_string(
    *,
    og_roster_id: int,
    season: str,
    round_number: int,
    receiving_roster_id: int,
    sending_roster_id: int,
) -> str:
    """
    Sleeper GraphQL pick format:

        original_roster,season,round,receiver,sender

    Example:
        5,2027,2,11,5
    """

    return ",".join(
        [
            str(og_roster_id),
            str(season),
            str(round_number),
            str(receiving_roster_id),
            str(sending_roster_id),
        ]
    )
