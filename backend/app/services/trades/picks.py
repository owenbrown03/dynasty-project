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
) -> str:
    """
    Build a human-readable label for one specific original draft pick.

    Example:
        2027 Round 2 (browntown333's original)
        2027 Round 2 (from Darven)
    """

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


async def get_current_pick_assets_by_league(
    *,
    sleeper,
    rosters_by_league_id: dict[str, list],
    pick_season: str,
    pick_round: int,
    roster_names_by_league_id: dict[str, dict[int, str]],
) -> dict[str, list[TradeDraftPickAsset]]:
    """
    Resolve current ownership of one pick year/round across leagues.

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
                str(pick_season),
                int(pick_round),
            ): roster.roster_id
            for roster in rosters
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
            if (
                str(traded_pick.season)
                != str(pick_season)
            ):
                continue

            if traded_pick.round != pick_round:
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

        for (
            og_roster_id,
            season,
            round_number,
        ), current_owner_roster_id in (
            pick_owner_by_key.items()
        ):
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
                    ),
                )
            )

        assets_by_league_id[league_id] = sorted(
            assets,
            key=lambda asset: (
                asset.current_owner_roster_id,
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