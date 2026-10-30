from __future__ import annotations

import asyncio
import logging
from types import SimpleNamespace
import time

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.sleeper.connection import (
    SleeperConnection,
)
from app.integrations.sleeper.client import SleeperClient
from app.integrations.sleeper.exceptions import SleeperGraphQLError
from app.models.db.ktc.models import KTCValue
from app.models.db.sleeper import api as model
from app.schemas.trades import (
    BulkTradeAvailabilityResponse,
    BulkTradeCounterparty,
    BulkTradeDropCandidate,
    BulkTradeLeagueAvailability,
    BulkTradeOfferRequest,
    BulkTradePickChoice,
    BulkTradePickRequest,
    BulkTradePlayerSearchResult,
    BulkTradeProposalRequest,
    BulkTradeProposalResponse,
    BulkTradeProposalResult,
)
from app.services.players.search import (
    search_local_dynasty_players,
)
from app.services.trades.picks import (
    build_sleeper_draft_pick_string,
    get_current_pick_assets_by_league,
    get_owned_matching_picks,
)
from app.services.trades.trade_dm import maybe_send_trade_dm
from app.services.waivers.dynasty import (
    DYNASTY_FANTASY_POSITIONS,
)
from app.utils.age import calculate_age
from app.crud.auth.user import get_draft_pick_projection_settings
from app.crud.sleeper.draft import (
    get_completed_draft_seasons_by_league_ids,
    get_drafts_by_league_ids,
)
from app.crud.sleeper.league import get_sync_states
from app.crud.sleeper.roster import get_all_rosters_by_league
from app.crud.sleeper.user import get_user_names_by_id
from app.infrastructure.redis.client import RedisClient
from app.models.db.auth import SiteUser
from app.services.draft.picks import (
    build_slot_by_roster_id,
    get_first_future_pick_season,
    get_league_draft_for_season,
)
from app.services.draft.projection import (
    build_cached_projected_pick_slots_by_roster_id,
    build_redraft_value_by_roster_id,
    redraft_projection_basis_for_method,
    redraft_value_system_active,
    resolve_draft_pick_projection_method,
)
from app.services.leagues.selection import (
    get_visible_owned_league_rows_by_sleeper_user_id,
    get_visible_owned_league_rows_by_username,
)

logger = logging.getLogger(__name__)


DEFAULT_TRADE_EXPIRY_SECONDS = 7 * 24 * 60 * 60
BULK_WRITE_DELAY_SECONDS = 1.0


def build_bulk_trade_result(
    *,
    league_id: str,
    counterparty_roster_id: int | None = None,
    success: bool,
    transaction_id: str | None = None,
    error: str | None = None,
) -> BulkTradeProposalResult:
    return BulkTradeProposalResult(
        league_id=league_id,
        counterparty_roster_id=counterparty_roster_id,
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
            dynasty_starter_war=result.dynasty_starter_war,
            dynasty_roster_war=result.dynasty_roster_war,
            redraft_starter_war=result.redraft_starter_war,
            redraft_roster_war=result.redraft_roster_war,
            my_dynasty_starter_war=result.my_dynasty_starter_war,
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


async def get_bulk_trade_target_players(
    *,
    db: AsyncSession,
    player_ids: list[str],
) -> list:
    seen_ids: set[str] = set()
    players = []

    for player_id in player_ids:
        if player_id in seen_ids:
            continue

        seen_ids.add(
            player_id,
        )
        players.append(
            await get_bulk_trade_target_player(
                db=db,
                player_id=player_id,
            )
        )

    return players


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


def build_target_player_results(
    players: list,
) -> list[BulkTradePlayerSearchResult]:
    return [
        build_target_player_result(
            player,
        )
        for player in players
    ]


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


def build_pick_choices_for_roster(
    *,
    owner_roster_id: int,
    pick_assets: list,
    requested_picks: list[BulkTradePickRequest],
    ) -> list[BulkTradePickChoice]:
    pick_choices: list[BulkTradePickChoice] = []

    for request_index, requested_pick in enumerate(
        requested_picks,
    ):
        matching_picks = [
            pick
            for pick in get_owned_matching_picks(
                pick_assets=pick_assets,
                owner_roster_id=owner_roster_id,
            )
            if (
                pick.season == requested_pick.season
                and pick.round == requested_pick.round
            )
        ]

        if not matching_picks:
            return []

        pick_choices.append(
            BulkTradePickChoice(
                request_index=request_index,
                season=requested_pick.season,
                round=requested_pick.round,
                matching_picks=matching_picks,
            )
        )

    return pick_choices


def get_counterparty_options(
    *,
    your_roster_id: int,
    league_rosters: list,
    pick_assets: list,
    requested_picks: list[BulkTradePickRequest],
    user_names_by_id: dict[str, str],
):
    """
    Backward-compatible helper for tests and older callers.

    Returns counterparties that can satisfy the full requested pick package,
    preserving one `BulkTradePickChoice` entry per requested pick.
    """

    counterparties = []

    for roster in league_rosters:
        if roster.roster_id == your_roster_id:
            continue

        pick_choices = build_pick_choices_for_roster(
            owner_roster_id=roster.roster_id,
            pick_assets=pick_assets,
            requested_picks=requested_picks,
        )

        if len(pick_choices) != len(requested_picks):
            continue

        counterparties.append(
            SimpleNamespace(
                roster_id=roster.roster_id,
                user_id=roster.owner_id,
                name=user_names_by_id.get(
                    roster.owner_id,
                    f"Roster {roster.roster_id}",
                ),
                pick_choices=pick_choices,
            )
        )

    return counterparties


def roster_has_all_players(
    *,
    roster,
    player_ids: list[str],
) -> bool:
    if not player_ids:
        return True

    roster_player_ids = set(
        roster.players or [],
    )

    return all(
        player_id in roster_player_ids
        for player_id in player_ids
    )


async def get_bulk_trade_availability(
    *,
    db: AsyncSession,
    connection: SleeperConnection,
    sleeper: SleeperClient,
    send_player_ids: list[str],
    send_picks: list[BulkTradePickRequest],
    receive_player_ids: list[str],
    receive_picks: list[BulkTradePickRequest],
    redis: RedisClient | None = None,
    site_user: SiteUser | None = None,
) -> BulkTradeAvailabilityResponse:
    if (
        len(send_player_ids) + len(send_picks) == 0
        or len(receive_player_ids) + len(receive_picks) == 0
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Select at least one asset on each side of the trade."
            ),
        )

    send_players = await get_bulk_trade_target_players(
        db=db,
        player_ids=send_player_ids,
    )
    receive_players = await get_bulk_trade_target_players(
        db=db,
        player_ids=receive_player_ids,
    )

    if connection.sleeper_user_id:
        owned_rows = await get_visible_owned_league_rows_by_sleeper_user_id(
            db=db,
            sleeper_user_id=connection.sleeper_user_id,
            site_user_id=connection.site_user_id,
            include_hidden=False,
        )
    elif connection.sleeper_username:
        owned_rows = await get_visible_owned_league_rows_by_username(
            db=db,
            username=connection.sleeper_username,
            site_user_id=connection.site_user_id,
            include_hidden=False,
        )
    else:
        owned_rows = []

    league_ids = [
        row.league.league_id
        for row in owned_rows
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

    has_picks = bool(send_picks or receive_picks)
    slots_by_league_id: dict[str, dict[tuple[str, int], int]] = {}
    projected_slots_by_league_id: dict[str, dict[tuple[str, int], int]] = {}

    if has_picks and league_ids:
        try:
            draft_pick_projection_settings = get_draft_pick_projection_settings(site_user)
            drafts_by_league_id = await get_drafts_by_league_ids(db, league_ids)
            completed_seasons_by_league_id = await get_completed_draft_seasons_by_league_ids(db, league_ids)
            sync_states_by_league_id = await get_sync_states(db, league_ids)

            requested_pick_seasons = {
                pick.season for pick in [*send_picks, *receive_picks]
            }

            for row in owned_rows:
                league = row.league
                league_id = league.league_id
                league_rosters = rosters_by_league.get(league_id, [])
                drafts = drafts_by_league_id.get(league_id, [])
                completed_seasons = completed_seasons_by_league_id.get(league_id, set())

                league_slots: dict[tuple[str, int], int] = {}
                for season in requested_pick_seasons:
                    slot_map = build_slot_by_roster_id(
                        draft=get_league_draft_for_season(drafts=drafts, season=season),
                        rosters=league_rosters,
                    )
                    for roster_id, slot in slot_map.items():
                        league_slots[(season, roster_id)] = slot
                if league_slots:
                    slots_by_league_id[league_id] = league_slots

                next_pick_season = get_first_future_pick_season(
                    league,
                    drafts=drafts,
                    completed_draft_seasons=completed_seasons,
                )

                if next_pick_season in requested_pick_seasons:
                    current_week = (
                        sync_states_by_league_id[league_id].last_synced_week
                        if league_id in sync_states_by_league_id
                        else int(
                            (league.settings or {}).get("last_scored_leg")
                            or (league.settings or {}).get("leg")
                            or 0
                        )
                    )

                    redraft_value_by_roster_id = None
                    if redraft_value_system_active(
                        current_week=current_week,
                        settings=draft_pick_projection_settings,
                    ):
                        redraft_value_by_roster_id = await build_redraft_value_by_roster_id(
                            db,
                            league_rosters,
                            basis=(
                                redraft_projection_basis_for_method(
                                    resolve_draft_pick_projection_method(
                                        current_week=current_week,
                                        settings=draft_pick_projection_settings,
                                    )
                                )
                                or "sleeper_projection"
                            ),
                        )

                    proj_result = await build_cached_projected_pick_slots_by_roster_id(
                        redis=redis,
                        league=league,
                        rosters=league_rosters,
                        current_week=current_week,
                        redraft_value_by_roster_id=redraft_value_by_roster_id,
                        settings=draft_pick_projection_settings,
                    )

                    if proj_result.slots_by_roster_id:
                        projected_slots_by_league_id[league_id] = {
                            (next_pick_season, roster_id): slot
                            for roster_id, slot in proj_result.slots_by_roster_id.items()
                        }
        except Exception as err:
            logger.warning(
                "Failed to calculate pick slot projections for bulk trades error=%s",
                err,
            )

    pick_assets_by_league_id = (
        await get_current_pick_assets_by_league(
            sleeper=sleeper,
            rosters_by_league_id=rosters_by_league,
            requested_picks=[
                *[
                    (
                        pick.season,
                        pick.round,
                    )
                    for pick in send_picks
                ],
                *[
                    (
                        pick.season,
                        pick.round,
                    )
                    for pick in receive_picks
                ],
            ],
            roster_names_by_league_id=(
                roster_names_by_league_id
            ),
            slots_by_league=slots_by_league_id,
            projected_slots_by_league=projected_slots_by_league_id,
        )
    )

    net_players = len(receive_player_ids) - len(send_player_ids)
    all_candidate_pids: set[str] = set()
    if net_players > 0:
        for row in owned_rows:
            all_candidate_pids.update(row.roster.players or [])

    drop_player_by_id: dict[str, model.Player] = {}
    drop_ktc_by_id: dict[str, KTCValue] = {}
    if all_candidate_pids:
        p_rows = (
            await db.execute(
                select(model.Player).where(
                    model.Player.player_id.in_(all_candidate_pids)
                )
            )
        ).scalars().all()
        drop_player_by_id = {p.player_id: p for p in p_rows}

        k_rows = (
            await db.execute(
                select(KTCValue).where(
                    KTCValue.player_id.in_(all_candidate_pids)
                )
            )
        ).scalars().all()
        drop_ktc_by_id = {k.player_id: k for k in k_rows}

    availability_rows = []

    for row in owned_rows:
        your_roster = row.roster
        league = row.league

        league_drop_candidates: list[BulkTradeDropCandidate] = []
        open_spots = your_roster.open_roster_spots(league)
        needed_drops = max(0, net_players - open_spots) if net_players > 0 else 0

        if net_players > 0 and your_roster.players:
            is_sf = "SUPER_FLEX" in (league.roster_positions or []) or (league.roster_positions or []).count("QB") >= 2
            parked_ids = set((your_roster.reserve or []) + (your_roster.taxi or [])) if not league.is_best_ball else set()
            eligible_pids = [
                pid for pid in your_roster.players
                if pid not in send_player_ids and pid not in parked_ids
            ]
            if not eligible_pids:
                eligible_pids = [
                    pid for pid in your_roster.players
                    if pid not in send_player_ids
                ]

            def _get_player_val(pid: str) -> float:
                k = drop_ktc_by_id.get(pid)
                if not k:
                    return 0.0
                val = k.sf_value if is_sf and k.sf_value is not None else k.value
                return float(val or 0.0)

            sorted_pids = sorted(
                eligible_pids,
                key=lambda pid: (
                    _get_player_val(pid),
                    drop_player_by_id.get(pid).full_name if drop_player_by_id.get(pid) else pid,
                ),
            )
            cut_pids = sorted_pids[:net_players]

            for pid in cut_pids:
                p = drop_player_by_id.get(pid)
                league_drop_candidates.append(
                    BulkTradeDropCandidate(
                        player_id=pid,
                        name=p.full_name if p else f"Player {pid}",
                        position=p.position if p else None,
                        team=p.team if p else None,
                        value=_get_player_val(pid),
                    )
                )
        league_rosters = rosters_by_league.get(
            league.league_id,
            [],
        )

        pick_assets = pick_assets_by_league_id.get(
            league.league_id,
            [],
        )
        if not roster_has_all_players(
            roster=your_roster,
            player_ids=send_player_ids,
        ):
            availability_rows.append(
                BulkTradeLeagueAvailability(
                    league_id=league.league_id,
                    league_name=league.name,
                    league_avatar=league.avatar,
                    your_roster_id=your_roster.roster_id,
                    your_faab_available=your_roster.faab_remaining(league),
                    is_eligible=False,
                    ineligibility_reason=(
                        "You do not roster every selected send player in this league."
                    ),
                )
            )
            continue

        send_pick_choices = build_pick_choices_for_roster(
            owner_roster_id=your_roster.roster_id,
            pick_assets=pick_assets,
            requested_picks=send_picks,
        )

        if len(send_pick_choices) != len(send_picks):
            availability_rows.append(
                BulkTradeLeagueAvailability(
                    league_id=league.league_id,
                    league_name=league.name,
                    league_avatar=league.avatar,
                    your_roster_id=your_roster.roster_id,
                    your_faab_available=your_roster.faab_remaining(league),
                    is_eligible=False,
                    ineligibility_reason=(
                        "You do not currently own every selected send pick in this league."
                    ),
                )
            )
            continue

        counterparty_options: list[BulkTradeCounterparty] = []

        for roster in league_rosters:
            if roster.roster_id == your_roster.roster_id:
                continue

            if not roster_has_all_players(
                roster=roster,
                player_ids=receive_player_ids,
            ):
                continue

            receive_pick_choices = build_pick_choices_for_roster(
                owner_roster_id=roster.roster_id,
                pick_assets=pick_assets,
                requested_picks=receive_picks,
            )

            if len(receive_pick_choices) != len(receive_picks):
                continue

            counterparty_options.append(
                BulkTradeCounterparty(
                    roster_id=roster.roster_id,
                    user_id=roster.owner_id,
                    name=user_names_by_id.get(
                        roster.owner_id,
                        f"Roster {roster.roster_id}",
                    ),
                    faab_available=roster.faab_remaining(league),
                    send_pick_choices=send_pick_choices,
                    receive_pick_choices=receive_pick_choices,
                )
            )

        if not counterparty_options:
            availability_rows.append(
                BulkTradeLeagueAvailability(
                    league_id=league.league_id,
                    league_name=league.name,
                    league_avatar=league.avatar,
                    your_roster_id=your_roster.roster_id,
                    your_faab_available=your_roster.faab_remaining(league),
                    open_roster_spots=open_spots,
                    needed_drops=needed_drops,
                    drop_candidates=league_drop_candidates,
                    is_eligible=False,
                    ineligibility_reason=(
                        "No single opposing roster can satisfy every selected receive asset in this league."
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
                your_faab_available=your_roster.faab_remaining(league),
                open_roster_spots=open_spots,
                needed_drops=needed_drops,
                drop_candidates=league_drop_candidates,
                is_eligible=True,
                counterparty_options=counterparty_options,
            )
        )

    return BulkTradeAvailabilityResponse(
        send_players=build_target_player_results(
            send_players,
        ),
        send_picks=send_picks,
        receive_players=build_target_player_results(
            receive_players,
        ),
        receive_picks=receive_picks,
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
    - The send-side players and picks are yours.
    - The receive-side players and picks belong to the selected counterparty.
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

    send_asset_count = (
        len(offer.send_player_ids)
        + len(offer.send_picks)
        + (1 if offer.send_faab > 0 else 0)
    )
    receive_asset_count = (
        len(offer.receive_player_ids)
        + len(offer.receive_picks)
        + (1 if offer.receive_faab > 0 else 0)
    )
    if send_asset_count == 0 or receive_asset_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Each bulk trade offer must include assets on both sides."
            ),
        )

    if not roster_has_all_players(
        roster=your_roster,
        player_ids=offer.send_player_ids,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "You no longer roster every selected send player in this league."
            ),
        )

    if not roster_has_all_players(
        roster=counterparty_roster,
        player_ids=offer.receive_player_ids,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The selected trade partner no longer owns every selected receive player."
            ),
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
            requested_picks=[
                (
                    pick.season,
                    pick.round,
                )
                for pick in [
                    *offer.send_picks,
                    *offer.receive_picks,
                ]
            ],
            roster_names_by_league_id=(
                roster_names_by_league_id
            ),
        )
    )

    pick_assets = pick_assets_by_league_id.get(
        offer.league_id,
        [],
    )

    def resolve_selected_picks(
        *,
        selected_picks,
        sender_roster_id: int,
        error_prefix: str,
    ) -> list:
        matching_picks = []

        for selected_pick in selected_picks:
            matching_pick = next(
                (
                    asset
                    for asset in pick_assets
                    if (
                        asset.season == selected_pick.season
                        and asset.round == selected_pick.round
                        and asset.og_roster_id == selected_pick.og_roster_id
                        and asset.current_owner_roster_id == sender_roster_id
                    )
                ),
                None,
            )

            if matching_pick is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"{error_prefix} "
                        f"{selected_pick.season} Round {selected_pick.round} "
                        f"pick from original roster "
                        f"{selected_pick.og_roster_id}."
                    ),
                )

            matching_picks.append(
                matching_pick,
            )

        return matching_picks

    send_matching_picks = resolve_selected_picks(
        selected_picks=offer.send_picks,
        sender_roster_id=your_roster.roster_id,
        error_prefix="You do not currently own the selected",
    )
    receive_matching_picks = resolve_selected_picks(
        selected_picks=offer.receive_picks,
        sender_roster_id=counterparty_roster.roster_id,
        error_prefix=(
            "The selected trade partner does not currently own the selected"
        ),
    )

    expires_at = (
        offer.expires_at
        if offer.expires_at is not None
        else int(time.time())
        + DEFAULT_TRADE_EXPIRY_SECONDS
    )

    draft_picks = [
        *[
            build_sleeper_draft_pick_string(
                og_roster_id=matching_pick.og_roster_id,
                season=matching_pick.season,
                round_number=matching_pick.round,
                receiving_roster_id=counterparty_roster.roster_id,
                sending_roster_id=your_roster.roster_id,
            )
            for matching_pick in send_matching_picks
        ],
        *[
            build_sleeper_draft_pick_string(
                og_roster_id=matching_pick.og_roster_id,
                season=matching_pick.season,
                round_number=matching_pick.round,
                receiving_roster_id=your_roster.roster_id,
                sending_roster_id=counterparty_roster.roster_id,
            )
            for matching_pick in receive_matching_picks
        ],
    ]

    waiver_budget: list[str] = []

    if offer.send_faab < 0 or offer.receive_faab < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="FAAB amount cannot be negative.",
        )

    if offer.send_faab > 0:
        your_available = (
            league.waiver_budget - your_roster.waiver_budget_used
        )
        if your_available < offer.send_faab:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"You do not have enough FAAB available (available: {your_available}, requested: {offer.send_faab})."
                ),
            )
        waiver_budget.append(
            f"{your_roster.roster_id},{counterparty_roster.roster_id},{offer.send_faab}"
        )

    if offer.receive_faab > 0:
        counterparty_available = (
            league.waiver_budget - counterparty_roster.waiver_budget_used
        )
        if counterparty_available < offer.receive_faab:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"The counterparty does not have enough FAAB available (available: {counterparty_available}, requested: {offer.receive_faab})."
                ),
            )
        waiver_budget.append(
            f"{counterparty_roster.roster_id},{your_roster.roster_id},{offer.receive_faab}"
        )

    return {
        "league_id": league.league_id,

        "k_adds": [
            *offer.send_player_ids,
            *offer.receive_player_ids,
        ],
        "v_adds": [
            *[
                counterparty_roster.roster_id
                for _ in offer.send_player_ids
            ],
            *[
                your_roster.roster_id
                for _ in offer.receive_player_ids
            ],
        ],

        "k_drops": [
            *offer.send_player_ids,
            *offer.receive_player_ids,
        ],
        "v_drops": [
            *[
                your_roster.roster_id
                for _ in offer.send_player_ids
            ],
            *[
                counterparty_roster.roster_id
                for _ in offer.receive_player_ids
            ],
        ],

        "draft_picks": draft_picks,

        "waiver_budget": waiver_budget,
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
                    counterparty_roster_id=offer.counterparty_roster_id,
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

    total_offers = len(validated_offers)

    for index, (offer, variables) in enumerate(
        validated_offers,
    ):
        try:
            response = await sleeper.write.propose_trade(
                **variables,
            )

            transaction_id = find_transaction_id(response)

            results.append(
                build_bulk_trade_result(
                    league_id=offer.league_id,
                    counterparty_roster_id=offer.counterparty_roster_id,
                    success=True,
                    transaction_id=transaction_id,
                )
            )

            player_map = (
                response.get("propose_trade", {}).get("player_map")
                if isinstance(response, dict)
                else None
            )

            await maybe_send_trade_dm(
                db=db,
                sleeper=sleeper,
                connection=connection,
                offer=offer,
                transaction_id=transaction_id,
                player_map=player_map,
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
                    counterparty_roster_id=offer.counterparty_roster_id,
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
                    counterparty_roster_id=offer.counterparty_roster_id,
                    success=False,
                    error=(
                        "Unexpected error while proposing "
                        "this trade."
                    ),
                )
            )

        if index < total_offers - 1:
            await asyncio.sleep(
                BULK_WRITE_DELAY_SECONDS,
            )

    return BulkTradeProposalResponse(
        results=results,
    )
