from __future__ import annotations

import logging
import time

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.sleeper.connection import (
    SleeperConnection,
)
from app.integrations.sleeper.client import SleeperClient
from app.integrations.sleeper.exceptions import SleeperGraphQLError
from app.models.db.sleeper import api as model
from app.schemas.trades import (
    BulkTradeAvailabilityResponse,
    BulkTradeCounterparty,
    BulkTradeLeagueAvailability,
    BulkTradeOfferRequest,
    BulkTradePlayerSearchResult,
    BulkTradeProposalRequest,
    BulkTradeProposalResponse,
    BulkTradeProposalResult,
    TradeDirection,
)
from app.services.players.search import (
    search_local_dynasty_players,
)
from app.services.trades.picks import (
    build_sleeper_draft_pick_string,
    get_current_pick_assets_by_league,
    get_owned_matching_picks,
)
from app.services.waivers.dynasty import (
    DYNASTY_FANTASY_POSITIONS,
)
from app.utils.age import calculate_age
from app.crud.sleeper.roster import get_all_rosters_by_league, get_owned_roster_rows, get_target_owner_roster
from app.crud.sleeper.user import get_user_names_by_id
from app.crud.sleeper.personal import get_league_sort_orders

logger = logging.getLogger(__name__)


DEFAULT_TRADE_EXPIRY_SECONDS = 7 * 24 * 60 * 60


def build_bulk_trade_result(
    *,
    league_id: str,
    success: bool,
    transaction_id: str | None = None,
    error: str | None = None,
) -> BulkTradeProposalResult:
    return BulkTradeProposalResult(
        league_id=league_id,
        success=success,
        transaction_id=transaction_id,
        error=error,
    )


async def search_bulk_trade_players(
    *,
    db: AsyncSession,
    query: str,
    limit: int = 10,
) -> list[BulkTradePlayerSearchResult]:
    results = await search_local_dynasty_players(
        db=db,
        query=query,
        limit=limit,
    )

    return [
        BulkTradePlayerSearchResult(
            player_id=result.player_id,
            name=result.name,
            position=result.position,
            team=result.team,
            age=result.age,
            ktc_value=result.ktc_value,
            fc_value=result.fc_value,
            underdog_position_rank=(
                result.underdog_position_rank
            ),
        )
        for result in results
    ]


async def get_bulk_trade_target_player(
    *,
    db: AsyncSession,
    player_id: str,
):
    result = await db.execute(
        select(model.Player).where(
            model.Player.player_id == player_id,
        )
    )

    player = result.scalar_one_or_none()

    if player is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "That player was not found in the local "
                "Sleeper player database."
            ),
        )

    if player.position not in DYNASTY_FANTASY_POSITIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Bulk trade offers currently support only "
                "QB, RB, WR, and TE players."
            ),
        )

    return player


def build_target_player_result(
    player,
) -> BulkTradePlayerSearchResult:
    return BulkTradePlayerSearchResult(
        player_id=player.player_id,
        name=player.full_name,
        position=player.position,
        team=player.team,
        age=calculate_age(
            player.birth_date,
        ),
    )


def build_roster_names_by_league_id(
    *,
    rosters_by_league_id,
    user_names_by_id: dict[str, str],
) -> dict[str, dict[int, str]]:
    """
    Roster IDs restart in every Sleeper league.

    This must stay nested by league_id. A flat roster_id -> name map causes
    roster 1 from one league to overwrite roster 1 from another league.
    """

    return {
        league_id: {
            roster.roster_id: user_names_by_id.get(
                roster.owner_id,
                f"Roster {roster.roster_id}",
            )
            for roster in rosters
        }
        for league_id, rosters in (
            rosters_by_league_id.items()
        )
    }


def get_counterparty_options(
    *,
    your_roster_id: int,
    league_rosters: list,
    pick_assets: list,
    user_names_by_id: dict[str, str],
) -> list[BulkTradeCounterparty]:
    """
    Sell flow: return every opposing roster that owns at least one matching
    price pick.
    """

    options = []

    for roster in league_rosters:
        if roster.roster_id == your_roster_id:
            continue

        matching_picks = get_owned_matching_picks(
            pick_assets=pick_assets,
            owner_roster_id=roster.roster_id,
        )

        if not matching_picks:
            continue

        options.append(
            BulkTradeCounterparty(
                roster_id=roster.roster_id,
                user_id=roster.owner_id,
                name=user_names_by_id.get(
                    roster.owner_id,
                    f"Roster {roster.roster_id}",
                ),
                matching_picks=matching_picks,
            )
        )

    return sorted(
        options,
        key=lambda option: option.name.lower(),
    )


async def get_bulk_trade_availability(
    *,
    db: AsyncSession,
    connection: SleeperConnection,
    sleeper: SleeperClient,
    player_id: str,
    direction: TradeDirection,
    pick_season: str,
    pick_round: int,
) -> BulkTradeAvailabilityResponse:
    """
    Builds buy/sell availability across all leagues owned by the connected
    Sleeper user.

    Buy:
    - Target player must be rostered by someone else.
    - You must currently own at least one matching pick.

    Sell:
    - You must currently own the target player.
    - At least one opposing roster must own a matching pick.
    """

    target_player = await get_bulk_trade_target_player(
        db=db,
        player_id=player_id,
    )

    owned_roster_rows = await get_owned_roster_rows(
        db=db,
        connection=connection,
    )

    if connection.sleeper_user_id:
        sort_order = await get_league_sort_orders(
            db=db,
            user_id=connection.sleeper_user_id,
        )
        owned_roster_rows.sort(
            key=lambda row: sort_order.get(
                row[1].league_id,
                9999,
            ),
        )

    league_ids = [
        league.league_id
        for _, league in owned_roster_rows
    ]

    rosters_by_league = await get_all_rosters_by_league(
        db=db,
        league_ids=league_ids,
    )

    user_ids = {
        roster.owner_id
        for league_rosters in (
            rosters_by_league.values()
        )
        for roster in league_rosters
        if roster.owner_id
    }

    user_names_by_id = await get_user_names_by_id(
        db=db,
        user_ids=user_ids,
    )

    roster_names_by_league_id = (
        build_roster_names_by_league_id(
            rosters_by_league_id=rosters_by_league,
            user_names_by_id=user_names_by_id,
        )
    )

    pick_assets_by_league_id = (
        await get_current_pick_assets_by_league(
            sleeper=sleeper,
            rosters_by_league_id=rosters_by_league,
            pick_season=pick_season,
            pick_round=pick_round,
            roster_names_by_league_id=(
                roster_names_by_league_id
            ),
        )
    )

    availability_rows = []

    for your_roster, league in owned_roster_rows:
        league_rosters = rosters_by_league.get(
            league.league_id,
            [],
        )

        pick_assets = pick_assets_by_league_id.get(
            league.league_id,
            [],
        )

        target_owner_roster = get_target_owner_roster(
            target_player_id=target_player.player_id,
            league_rosters=league_rosters,
        )

        you_own_target_player = (
            target_owner_roster is not None
            and target_owner_roster.roster_id
            == your_roster.roster_id
        )

        # --------------------------------------------------
        # Buy
        # --------------------------------------------------
        if direction == TradeDirection.BUY:
            if target_owner_roster is None:
                availability_rows.append(
                    BulkTradeLeagueAvailability(
                        league_id=league.league_id,
                        league_name=league.name,
                        league_avatar=league.avatar,

                        your_roster_id=your_roster.roster_id,

                        you_own_target_player=False,

                        is_eligible=False,
                        ineligibility_reason=(
                            "Player is not rostered in this league."
                        ),
                    )
                )
                continue

            if you_own_target_player:
                availability_rows.append(
                    BulkTradeLeagueAvailability(
                        league_id=league.league_id,
                        league_name=league.name,
                        league_avatar=league.avatar,

                        your_roster_id=your_roster.roster_id,

                        target_owner_roster_id=(
                            target_owner_roster.roster_id
                        ),
                        target_owner_user_id=(
                            target_owner_roster.owner_id
                        ),
                        target_owner_name=(
                            user_names_by_id.get(
                                target_owner_roster.owner_id,
                                f"Roster {target_owner_roster.roster_id}",
                            )
                        ),

                        you_own_target_player=True,

                        is_eligible=False,
                        ineligibility_reason=(
                            "You already roster this player."
                        ),
                    )
                )
                continue

            matching_picks = get_owned_matching_picks(
                pick_assets=pick_assets,
                owner_roster_id=your_roster.roster_id,
            )

            if not matching_picks:
                availability_rows.append(
                    BulkTradeLeagueAvailability(
                        league_id=league.league_id,
                        league_name=league.name,
                        league_avatar=league.avatar,

                        your_roster_id=your_roster.roster_id,

                        target_owner_roster_id=(
                            target_owner_roster.roster_id
                        ),
                        target_owner_user_id=(
                            target_owner_roster.owner_id
                        ),
                        target_owner_name=(
                            user_names_by_id.get(
                                target_owner_roster.owner_id,
                                f"Roster {target_owner_roster.roster_id}",
                            )
                        ),

                        you_own_target_player=False,

                        is_eligible=False,
                        ineligibility_reason=(
                            f"You do not currently own a tradable "
                            f"{pick_season} Round {pick_round} pick."
                        ),
                    )
                )
                continue

            availability_rows.append(
                BulkTradeLeagueAvailability(
                    league_id=league.league_id,
                    league_name=league.name,
                    league_avatar=league.avatar,

                    your_roster_id=your_roster.roster_id,

                    target_owner_roster_id=(
                        target_owner_roster.roster_id
                    ),
                    target_owner_user_id=(
                        target_owner_roster.owner_id
                    ),
                    target_owner_name=(
                        user_names_by_id.get(
                            target_owner_roster.owner_id,
                            f"Roster {target_owner_roster.roster_id}",
                        )
                    ),

                    you_own_target_player=False,

                    is_eligible=True,
                    matching_picks=matching_picks,
                )
            )
            continue

        # --------------------------------------------------
        # Sell
        # --------------------------------------------------
        if not you_own_target_player:
            availability_rows.append(
                BulkTradeLeagueAvailability(
                    league_id=league.league_id,
                    league_name=league.name,
                    league_avatar=league.avatar,

                    your_roster_id=your_roster.roster_id,

                    target_owner_roster_id=(
                        target_owner_roster.roster_id
                        if target_owner_roster is not None
                        else None
                    ),
                    target_owner_user_id=(
                        target_owner_roster.owner_id
                        if target_owner_roster is not None
                        else None
                    ),
                    target_owner_name=(
                        user_names_by_id.get(
                            target_owner_roster.owner_id,
                            f"Roster {target_owner_roster.roster_id}",
                        )
                        if target_owner_roster is not None
                        else None
                    ),

                    you_own_target_player=False,

                    is_eligible=False,
                    ineligibility_reason=(
                        "You do not roster this player in this league."
                    ),
                )
            )
            continue

        counterparty_options = get_counterparty_options(
            your_roster_id=your_roster.roster_id,
            league_rosters=league_rosters,
            pick_assets=pick_assets,
            user_names_by_id=user_names_by_id,
        )

        if not counterparty_options:
            availability_rows.append(
                BulkTradeLeagueAvailability(
                    league_id=league.league_id,
                    league_name=league.name,
                    league_avatar=league.avatar,

                    your_roster_id=your_roster.roster_id,

                    you_own_target_player=True,

                    is_eligible=False,
                    ineligibility_reason=(
                        f"No opposing roster currently owns a "
                        f"tradable {pick_season} Round {pick_round} pick."
                    ),
                )
            )
            continue

        availability_rows.append(
            BulkTradeLeagueAvailability(
                league_id=league.league_id,
                league_name=league.name,
                league_avatar=league.avatar,

                your_roster_id=your_roster.roster_id,

                you_own_target_player=True,

                is_eligible=True,
                counterparty_options=counterparty_options,
            )
        )

    return BulkTradeAvailabilityResponse(
        player=build_target_player_result(
            target_player,
        ),
        direction=direction,
        pick_season=str(
            pick_season,
        ),
        pick_round=pick_round,
        leagues=availability_rows,
    )


async def validate_and_build_trade_variables(
    *,
    db: AsyncSession,
    connection: SleeperConnection,
    sleeper: SleeperClient,
    offer: BulkTradeOfferRequest,
) -> dict:
    """
    Validates one offer against the current database state.

    It confirms:
    - You own the submitting roster.
    - The counterparty exists.
    - The target player is on the correct side.
    - The selected original pick is currently owned by the sending roster.
    """

    if not connection.sleeper_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Connected Sleeper account is missing a "
                "Sleeper user ID."
            ),
        )

    owned_result = await db.execute(
        select(
            model.Roster,
            model.League,
        )
        .join(
            model.League,
            model.League.league_id
            == model.Roster.league_id,
        )
        .where(
            model.Roster.league_id == offer.league_id,
            model.Roster.roster_id
            == offer.your_roster_id,
            model.Roster.owner_id
            == connection.sleeper_user_id,
        )
    )

    owned_row = owned_result.one_or_none()

    if owned_row is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not own the selected roster in this league."
            ),
        )

    your_roster, league = owned_row

    league_rosters_result = await db.execute(
        select(model.Roster).where(
            model.Roster.league_id == offer.league_id,
        )
    )

    league_rosters = list(
        league_rosters_result.scalars(),
    )

    counterparty_roster = next(
        (
            roster
            for roster in league_rosters
            if roster.roster_id
            == offer.counterparty_roster_id
        ),
        None,
    )

    if counterparty_roster is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The selected trade partner no longer exists "
                "in this league."
            ),
        )

    if (
        counterparty_roster.roster_id
        == your_roster.roster_id
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "You cannot propose a trade to your own roster."
            ),
        )

    target_owner_roster = get_target_owner_roster(
        target_player_id=offer.target_player_id,
        league_rosters=league_rosters,
    )

    if offer.direction == TradeDirection.BUY:
        if target_owner_roster is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "The target player is not rostered in this league."
                ),
            )

        if (
            target_owner_roster.roster_id
            != counterparty_roster.roster_id
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "The selected trade partner no longer owns "
                    "the target player."
                ),
            )

        pick_sender_roster_id = your_roster.roster_id
        pick_receiver_roster_id = (
            counterparty_roster.roster_id
        )

        player_sender_roster_id = (
            counterparty_roster.roster_id
        )
        player_receiver_roster_id = your_roster.roster_id

    else:
        if (
            target_owner_roster is None
            or target_owner_roster.roster_id
            != your_roster.roster_id
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "You no longer roster the target player "
                    "in this league."
                ),
            )

        pick_sender_roster_id = (
            counterparty_roster.roster_id
        )
        pick_receiver_roster_id = your_roster.roster_id

        player_sender_roster_id = your_roster.roster_id
        player_receiver_roster_id = (
            counterparty_roster.roster_id
        )

    user_ids = {
        roster.owner_id
        for roster in league_rosters
        if roster.owner_id
    }

    user_names_by_id = await get_user_names_by_id(
        db=db,
        user_ids=user_ids,
    )

    roster_names_by_league_id = {
        offer.league_id: {
            roster.roster_id: user_names_by_id.get(
                roster.owner_id,
                f"Roster {roster.roster_id}",
            )
            for roster in league_rosters
        }
    }

    pick_assets_by_league_id = (
        await get_current_pick_assets_by_league(
            sleeper=sleeper,
            rosters_by_league_id={
                offer.league_id: league_rosters,
            },
            pick_season=offer.pick.season,
            pick_round=offer.pick.round,
            roster_names_by_league_id=(
                roster_names_by_league_id
            ),
        )
    )

    pick_assets = pick_assets_by_league_id.get(
        offer.league_id,
        [],
    )

    matching_pick = next(
        (
            asset
            for asset in pick_assets
            if (
                asset.og_roster_id
                == offer.pick.og_roster_id
                and asset.current_owner_roster_id
                == pick_sender_roster_id
            )
        ),
        None,
    )

    if matching_pick is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"You do not currently own the selected "
                f"{offer.pick.season} Round {offer.pick.round} "
                f"pick from original roster "
                f"{offer.pick.og_roster_id}."
            ),
        )

    expires_at = (
        offer.expires_at
        if offer.expires_at is not None
        else int(time.time())
        + DEFAULT_TRADE_EXPIRY_SECONDS
    )

    draft_pick = build_sleeper_draft_pick_string(
        og_roster_id=matching_pick.og_roster_id,
        season=matching_pick.season,
        round_number=matching_pick.round,
        receiving_roster_id=pick_receiver_roster_id,
        sending_roster_id=pick_sender_roster_id,
    )

    return {
        "league_id": league.league_id,

        "k_adds": [
            offer.target_player_id,
        ],
        "v_adds": [
            player_receiver_roster_id,
        ],

        "k_drops": [
            offer.target_player_id,
        ],
        "v_drops": [
            player_sender_roster_id,
        ],

        "draft_picks": [
            draft_pick,
        ],

        "waiver_budget": [],
        "expires_at": expires_at,
    }


def find_transaction_id(
    payload,
) -> str | None:
    """
    Handles minor GraphQL response-shape differences safely.
    """

    if isinstance(payload, dict):
        transaction_id = payload.get(
            "transaction_id",
        )

        if transaction_id:
            return str(
                transaction_id,
            )

        for value in payload.values():
            found = find_transaction_id(
                value,
            )

            if found:
                return found

    if isinstance(payload, list):
        for value in payload:
            found = find_transaction_id(
                value,
            )

            if found:
                return found

    return None


async def submit_bulk_trade_offers(
    *,
    db: AsyncSession,
    connection: SleeperConnection | None,
    sleeper: SleeperClient,
    request: BulkTradeProposalRequest,
) -> BulkTradeProposalResponse:
    """
    Two-pass bulk submission.

    Pass 1:
        Validate every selected offer.

    Pass 2:
        Only submit if every selected offer passed validation.

    This is not truly atomic at Sleeper's API level, but it prevents us from
    knowingly sending valid offers while another selected offer is invalid.
    """

    if connection is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Connect a Sleeper account before proposing trades."
            ),
        )

    seen_league_ids = set()

    for offer in request.offers:
        if offer.league_id in seen_league_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Bulk trade requests can include only "
                    "one offer per league."
                ),
            )

        seen_league_ids.add(
            offer.league_id,
        )

    validated_offers: list[
        tuple[
            BulkTradeOfferRequest,
            dict,
        ]
    ] = []

    preflight_errors_by_league_id: dict[
        str,
        str,
    ] = {}

    # --------------------------------------------------
    # First pass: validate every selected offer.
    # --------------------------------------------------
    for offer in request.offers:
        try:
            variables = (
                await validate_and_build_trade_variables(
                    db=db,
                    connection=connection,
                    sleeper=sleeper,
                    offer=offer,
                )
            )

            validated_offers.append(
                (
                    offer,
                    variables,
                )
            )

        except HTTPException as error:
            preflight_errors_by_league_id[
                offer.league_id
            ] = str(
                error.detail,
            )

        except Exception:
            logger.exception(
                "Trade preflight failed league=%s",
                offer.league_id,
            )

            preflight_errors_by_league_id[
                offer.league_id
            ] = (
                "Unable to validate this trade before submission."
            )

    # --------------------------------------------------
    # Do not send anything if any selected offer failed.
    # --------------------------------------------------
    if preflight_errors_by_league_id:
        return BulkTradeProposalResponse(
            results=[
                build_bulk_trade_result(
                    league_id=offer.league_id,
                    success=False,
                    error=(
                        preflight_errors_by_league_id.get(
                            offer.league_id,
                            (
                                "Not sent because another selected "
                                "trade failed validation."
                            ),
                        )
                    ),
                )
                for offer in request.offers
            ]
        )

    # --------------------------------------------------
    # Second pass: all selected offers are valid locally.
    # --------------------------------------------------
    results = []

    for offer, variables in validated_offers:
        try:
            response = await sleeper.write.propose_trade(
                **variables,
            )

            results.append(
                build_bulk_trade_result(
                    league_id=offer.league_id,
                    success=True,
                    transaction_id=find_transaction_id(
                        response,
                    ),
                )
            )

        except SleeperGraphQLError as error:
            logger.warning(
                (
                    "Sleeper rejected bulk trade "
                    "league=%s error=%s"
                ),
                offer.league_id,
                error,
            )

            results.append(
                build_bulk_trade_result(
                    league_id=offer.league_id,
                    success=False,
                    error=str(error),
                )
            )

        except Exception:
            logger.exception(
                "Bulk trade proposal failed league=%s",
                offer.league_id,
            )

            results.append(
                build_bulk_trade_result(
                    league_id=offer.league_id,
                    success=False,
                    error=(
                        "Unexpected error while proposing "
                        "this trade."
                    ),
                )
            )

    return BulkTradeProposalResponse(
        results=results,
    )
