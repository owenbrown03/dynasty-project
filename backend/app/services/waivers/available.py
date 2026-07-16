from __future__ import annotations
from collections.abc import Iterable

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.war.redraft.models import PlayerWAR
from app.analytics.war.redraft.service import WARService
from app.analytics.war.dynasty.models import DynastyProjection
from app.crud.auth.user import get_war_value_settings_by_user_id
from app.crud.value import get_player_values
from app.infrastructure.redis.client import RedisClient
from app.models.db.sleeper.api import League, Roster
from app.models.db.sleeper.connection import SleeperConnection
from app.schemas.waivers import (
    WaiverAvailableLeagueAvailability,
    WaiverAvailablePlayer,
    WaiverAvailablePlayersResponse,
    WaiverLeagueOption,
    WaiverRosterPlayer,
    WaiverRosterPlayersResponse,
)
from app.services.values.basis import (
    ValueBasis,
    get_player_value,
    get_value_label,
)
from app.services.personal_values import hydrate_personal_player_values
from app.services.leagues.selection import (
    get_visible_owned_league_rows_by_sleeper_user_id,
)
from app.services.war.shared import (
    build_cached_dynasty_projections_by_player_id,
    build_shared_redraft_war_by_league_id,
)
from app.services.waivers.dynasty import (
    DYNASTY_FANTASY_POSITIONS,
)


def build_league_option(
    *,
    roster: Roster,
    league: League,
) -> WaiverLeagueOption:
    faab_budget = league.waiver_budget
    faab_remaining = roster.faab_remaining(league)

    faab_percent_remaining = 0.0

    if faab_budget > 0:
        faab_percent_remaining = round(
            (faab_remaining / faab_budget) * 100,
            1,
        )

    roster_capacity = roster.claimable_roster_capacity(
        league,
    )

    return WaiverLeagueOption(
        league_id=league.league_id,
        league_name=league.name,
        league_avatar=league.avatar,

        roster_id=roster.roster_id,

        roster_size=roster.roster_size,
        roster_capacity=roster_capacity,
        roster_spots_available=roster.open_roster_spots(
            league,
        ),

        faab_remaining=faab_remaining,
        faab_percent_remaining=faab_percent_remaining,
    )


async def get_waiver_league_options(
    *,
    db: AsyncSession,
    connection: SleeperConnection,
) -> list[WaiverLeagueOption]:
    """
    Returns every league roster owned by the connected Sleeper account.

    This is intentionally lightweight so the frontend can use it to
    populate the league selector before loading a full available-player
    table.
    """

    if not connection.sleeper_user_id:
        return []

    owned_rows = await get_visible_owned_league_rows_by_sleeper_user_id(
        db=db,
        sleeper_user_id=connection.sleeper_user_id,
        site_user_id=connection.site_user_id,
    )

    return [
        build_league_option(
            roster=row.roster,
            league=row.league,
        )
        for row in owned_rows
    ]


async def get_owned_waiver_league(
    *,
    db: AsyncSession,
    connection: SleeperConnection,
    league_id: str,
) -> tuple[Roster, League]:
    """
    Returns the connected user's roster in one selected league.

    The ownership requirement matters because this endpoint exposes a
    roster-specific claimable-player view.
    """

    if not connection.sleeper_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Connected Sleeper account is missing a Sleeper user ID."
            ),
        )

    result = await db.execute(
        select(Roster, League)
        .join(
            League,
            League.league_id == Roster.league_id,
        )
        .where(
            Roster.league_id == league_id,
            Roster.owner_id == connection.sleeper_user_id,
        )
    )

    row = result.one_or_none()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No owned roster was found for this league."
            ),
        )

    return row


async def get_rostered_player_ids(
    *,
    db: AsyncSession,
    league_id: str,
) -> set[str]:
    """
    A player is available only when they are not on any roster in the
    selected Sleeper league.
    """

    result = await db.execute(
        select(Roster.players).where(
            Roster.league_id == league_id,
        )
    )

    return {
        player_id
        for player_ids in result.scalars()
        for player_id in (player_ids or [])
        if player_id
    }


def get_available_war_players(
    *,
    war_players: Iterable[PlayerWAR],
    rostered_player_ids: set[str],
) -> list[PlayerWAR]:
    """
    Filters the league WAR universe down to claimable QB/RB/WR/TE players.

    Custom placeholder spots, IDP positions, DEF, K, and other unsupported
    positions stay out of this version of the waiver player table.
    """

    return [
        player
        for player in war_players
        if (
            player.player_id not in rostered_player_ids
            and player.position in DYNASTY_FANTASY_POSITIONS
        )
    ]


async def project_full_available_dynasty_pool(
    *,
    redis: RedisClient | None,
    available_war_players: Iterable[PlayerWAR],
) -> dict[str, DynastyProjection]:
    """
    Option A: calculate dynasty WAR for every available supported player
    in the selected league.

    This is intentionally complete, not candidate-limited, so sorting by
    dynasty WAR in the detailed table is accurate.
    """

    return await build_cached_dynasty_projections_by_player_id(
        redis=redis,
        player_wars=list(available_war_players),
    )


def sort_available_players(
    *,
    players: list[WaiverAvailablePlayer],
) -> list[WaiverAvailablePlayer]:
    """
    Sort selected values descending while keeping missing values at the end.

    Negative WAR values remain correctly ordered below positive WAR values.
    """

    return sorted(
        players,
        key=lambda player: (
            player.selected_value is None,
            -(
                player.selected_value
                if player.selected_value is not None
                else 0.0
            ),
            player.name.lower(),
        ),
    )


def build_claim_blocked_reason(
    *,
    roster_spots_available: int,
) -> str | None:
    if roster_spots_available >= 0:
        return None

    return (
        f"This roster is {abs(roster_spots_available)} "
        "players over capacity. Remove players before claiming."
    )


async def build_available_players_for_league(
    *,
    db: AsyncSession,
    redis: RedisClient,
    connection: SleeperConnection,
    roster: Roster,
    league: League,
    value_basis: ValueBasis,
    war_service: WARService,
    redraft_war_players: list[PlayerWAR] | None = None,
    war_value_settings=None,
) -> tuple[list[WaiverAvailablePlayer], str]:
    rostered_player_ids = await get_rostered_player_ids(
        db=db,
        league_id=league.league_id,
    )

    if redraft_war_players is None:
        redraft_war_players = await war_service.calculate(
            db=db,
            redis=redis,
            league_id=league.league_id,
        )

    available_war_players = get_available_war_players(
        war_players=redraft_war_players,
        rostered_player_ids=rostered_player_ids,
    )

    available_player_ids = [
        player.player_id
        for player in available_war_players
    ]

    dynasty_war_by_player_id = (
        await project_full_available_dynasty_pool(
            redis=redis,
            available_war_players=available_war_players,
        )
    )
    if war_value_settings is None:
        war_value_settings = await get_war_value_settings_by_user_id(
            db=db,
            site_user_id=connection.site_user_id,
        )

    player_values = await get_player_values(
        db=db,
        player_ids=available_player_ids,
        redraft_war_players=redraft_war_players,
        dynasty_war_by_player_id=dynasty_war_by_player_id,
    )
    if value_basis == ValueBasis.MY_WAR:
        player_values = await hydrate_personal_player_values(
            db=db,
            site_user_id=connection.site_user_id,
            league=league,
            player_values=player_values,
            redis=redis,
        )

    roster_spots_available = roster.open_roster_spots(
        league,
    )
    claim_blocked_reason = build_claim_blocked_reason(
        roster_spots_available=roster_spots_available,
    )
    faab_remaining = roster.faab_remaining(league)
    faab_percent_remaining = 0.0

    if league.waiver_budget > 0:
        faab_percent_remaining = round(
            (faab_remaining / league.waiver_budget) * 100,
            1,
        )

    available_players: list[WaiverAvailablePlayer] = []

    for player in player_values:
        selected_value = get_player_value(
            player=player,
            basis=value_basis,
            war_value_settings=war_value_settings,
        )

        available_players.append(
            WaiverAvailablePlayer(
                **player.model_dump(),
                league_id=league.league_id,
                league_name=league.name,
                league_avatar=league.avatar,
                roster_id=roster.roster_id,
                roster_size=roster.roster_size,
                roster_capacity=roster.claimable_roster_capacity(
                    league,
                ),
                roster_spots_available=roster_spots_available,
                faab_remaining=faab_remaining,
                faab_percent_remaining=faab_percent_remaining,
                can_submit_claim=claim_blocked_reason is None,
                claim_blocked_reason=claim_blocked_reason,
                selected_value=selected_value,
            )
        )

    return available_players, get_value_label(
        value_basis,
        war_value_settings,
    )


def aggregate_available_players_by_player_id(
    *,
    players: list[WaiverAvailablePlayer],
) -> list[WaiverAvailablePlayer]:
    aggregated_by_player_id: dict[
        str,
        dict[str, object],
    ] = {}

    for player in players:
        league_availability = (
            WaiverAvailableLeagueAvailability(
                league_id=player.league_id or '',
                league_name=player.league_name or '',
                league_avatar=player.league_avatar,
                roster_id=player.roster_id or 0,
                roster_size=player.roster_size or 0,
                roster_capacity=(
                    player.roster_capacity or 0
                ),
                roster_spots_available=(
                    player.roster_spots_available
                    or 0
                ),
                faab_remaining=player.faab_remaining or 0,
                faab_percent_remaining=(
                    player.faab_percent_remaining
                    or 0.0
                ),
                can_submit_claim=player.can_submit_claim,
                claim_blocked_reason=(
                    player.claim_blocked_reason
                ),
                selected_value=player.selected_value,
            )
        )

        existing = aggregated_by_player_id.get(
            player.player_id,
        )

        if existing is None:
            aggregated_by_player_id[
                player.player_id
            ] = {
                **player.model_dump(),
                "league_id": None,
                "league_name": None,
                "league_avatar": None,
                "roster_id": None,
                "roster_size": None,
                "roster_capacity": None,
                "roster_spots_available": None,
                "faab_remaining": None,
                "faab_percent_remaining": None,
                "can_submit_claim": True,
                "claim_blocked_reason": None,
                "league_count": 1,
                "league_availability": [
                    league_availability
                ],
            }
            continue

        existing_availability = existing[
            "league_availability"
        ]
        assert isinstance(
            existing_availability,
            list,
        )
        existing_availability.append(
            league_availability
        )
        existing["league_count"] = (
            int(existing["league_count"]) + 1
        )

        existing_value = existing.get(
            "selected_value",
        )
        next_value = player.selected_value

        if (
            existing_value is None
            or (
                next_value is not None
                and next_value > existing_value
            )
        ):
            existing.update(
                {
                    "selected_value": next_value,
                    "redraft_starter_war": (
                        player.redraft_starter_war
                    ),
                    "redraft_roster_war": (
                        player.redraft_roster_war
                    ),
                    "dynasty_starter_war": (
                        player.dynasty_starter_war
                    ),
                    "dynasty_roster_war": (
                        player.dynasty_roster_war
                    ),
                    "my_redraft_starter_war": (
                        player.my_redraft_starter_war
                    ),
                    "my_redraft_roster_war": (
                        player.my_redraft_roster_war
                    ),
                    "my_dynasty_starter_war": (
                        player.my_dynasty_starter_war
                    ),
                    "my_dynasty_roster_war": (
                        player.my_dynasty_roster_war
                    ),
                }
            )

    aggregated_players = [
        WaiverAvailablePlayer(**player)
        for player in aggregated_by_player_id.values()
    ]

    for player in aggregated_players:
        player.league_availability.sort(
            key=lambda availability: (
                availability.selected_value is None,
                -(
                    availability.selected_value
                    if availability.selected_value
                    is not None
                    else 0.0
                ),
                availability.league_name.lower(),
            ),
        )

    return aggregated_players


async def get_available_waiver_players(
    *,
    db: AsyncSession,
    redis: RedisClient,
    connection: SleeperConnection,
    league_id: str | None,
    value_basis: ValueBasis,
    war_service: WARService,
    page: int = 1,
    page_size: int = 50,
) -> WaiverAvailablePlayersResponse:
    """
    Returns all available QB/RB/WR/TE players for one owned league.

    Every returned player includes:
    - KTC
    - FantasyCalc
    - Underdog position rank
    - current redraft WAR
    - full dynasty WAR
    - selected_value based on value_basis
    """

    safe_page = max(page, 1)
    safe_page_size = max(page_size, 1)

    if league_id:
        roster, league = await get_owned_waiver_league(
            db=db,
            connection=connection,
            league_id=league_id,
        )

        available_players, value_label = (
            await build_available_players_for_league(
                db=db,
                redis=redis,
                connection=connection,
                roster=roster,
                league=league,
                value_basis=value_basis,
                war_service=war_service,
            )
        )

        sorted_players = sort_available_players(
            players=available_players,
        )
        total_players = len(sorted_players)
        total_pages = max(
            1,
            (
                total_players
                + safe_page_size
                - 1
            ) // safe_page_size,
        )
        current_page = min(
            safe_page,
            total_pages,
        )
        page_start = (
            current_page - 1
        ) * safe_page_size
        paged_players = sorted_players[
            page_start:page_start + safe_page_size
        ]

        return WaiverAvailablePlayersResponse(
            league_id=league.league_id,
            league_name=league.name,
            league_avatar=league.avatar,
            roster_id=roster.roster_id,
            is_all_leagues=False,
            value_basis=value_basis,
            value_label=value_label,
            page=current_page,
            page_size=safe_page_size,
            total_pages=total_pages,
            total_players=total_players,
            players=paged_players,
        )

    if not connection.sleeper_user_id:
        return WaiverAvailablePlayersResponse(
            league_name="All visible leagues",
            is_all_leagues=True,
            value_basis=value_basis,
            value_label=get_value_label(
                value_basis,
                await get_war_value_settings_by_user_id(
                    db=db,
                    site_user_id=connection.site_user_id,
                ),
            ),
            page=safe_page,
            page_size=safe_page_size,
            total_pages=0,
            total_players=0,
        )

    owned_rows = await get_visible_owned_league_rows_by_sleeper_user_id(
        db=db,
        sleeper_user_id=connection.sleeper_user_id,
        site_user_id=connection.site_user_id,
    )

    all_available_players: list[WaiverAvailablePlayer] = []
    war_value_settings = await get_war_value_settings_by_user_id(
        db=db,
        site_user_id=connection.site_user_id,
    )
    value_label = get_value_label(
        value_basis,
        war_value_settings,
    )
    redraft_war_by_league_id = (
        await build_shared_redraft_war_by_league_id(
            db=db,
            leagues=[
                row.league
                for row in owned_rows
            ],
            war_service=war_service,
        )
    )

    for row in owned_rows:
        league_players, value_label = (
            await build_available_players_for_league(
                db=db,
                redis=redis,
                connection=connection,
                roster=row.roster,
                league=row.league,
                value_basis=value_basis,
                war_service=war_service,
                redraft_war_players=(
                    redraft_war_by_league_id[
                        row.league.league_id
                    ]
                ),
                war_value_settings=war_value_settings,
            )
        )
        all_available_players.extend(
            league_players,
        )

    aggregated_players = (
        aggregate_available_players_by_player_id(
            players=all_available_players,
        )
    )
    sorted_players = sort_available_players(
        players=aggregated_players,
    )
    total_players = len(sorted_players)
    total_pages = max(
        1,
        (
            total_players
            + safe_page_size
            - 1
        ) // safe_page_size,
    )
    current_page = min(
        safe_page,
        total_pages,
    )
    page_start = (
        current_page - 1
    ) * safe_page_size
    paged_players = sorted_players[
        page_start:page_start + safe_page_size
    ]

    return WaiverAvailablePlayersResponse(
        league_name="All visible leagues",
        is_all_leagues=True,
        value_basis=value_basis,
        value_label=value_label,
        page=current_page,
        page_size=safe_page_size,
        total_pages=total_pages,
        total_players=total_players,
        players=paged_players,
    )


async def get_roster_waiver_players(
    *,
    db: AsyncSession,
    redis: RedisClient,
    connection: SleeperConnection,
    league_id: str,
    value_basis: ValueBasis,
    war_service: WARService,
) -> WaiverRosterPlayersResponse:
    """
    Returns QB/RB/WR/TE players on the connected user's roster.

    The detailed waiver claim modal uses this response to let the user
    choose a drop player. Results are sorted from lowest to highest based
    on the selected valuation system, making the weakest player appear
    first by default.
    """

    roster, league = await get_owned_waiver_league(
        db=db,
        connection=connection,
        league_id=league_id,
    )

    redraft_war_players = await war_service.calculate(
        db=db,
        redis=redis,
        league_id=league_id,
    )

    redraft_war_by_player_id = {
        player.player_id: player
        for player in redraft_war_players
    }

    roster_war_players = [
        redraft_war_by_player_id[player_id]
        for player_id in (roster.players or [])
        if (
            player_id in redraft_war_by_player_id
            and redraft_war_by_player_id[player_id].position
            in DYNASTY_FANTASY_POSITIONS
        )
    ]

    roster_player_ids = [
        player.player_id
        for player in roster_war_players
    ]

    dynasty_war_by_player_id = (
        await project_full_available_dynasty_pool(
            redis=redis,
            available_war_players=roster_war_players,
        )
    )
    war_value_settings = await get_war_value_settings_by_user_id(
        db=db,
        site_user_id=connection.site_user_id,
    )

    player_values = await get_player_values(
        db=db,
        player_ids=roster_player_ids,
        redraft_war_players=redraft_war_players,
        dynasty_war_by_player_id=dynasty_war_by_player_id,
    )
    if value_basis == ValueBasis.MY_WAR:
        player_values = await hydrate_personal_player_values(
            db=db,
            site_user_id=connection.site_user_id,
            league=league,
            player_values=player_values,
            redis=redis,
        )

    roster_players: list[WaiverRosterPlayer] = []

    for player in player_values:
        selected_value = get_player_value(
            player=player,
            basis=value_basis,
            war_value_settings=war_value_settings,
        )

        roster_players.append(
            WaiverRosterPlayer(
                **player.model_dump(),
                selected_value=selected_value,
            )
        )

    roster_players.sort(
        key=lambda player: (
            player.selected_value is None,
            (
                player.selected_value
                if player.selected_value is not None
                else 0.0
            ),
            player.name.lower(),
        )
    )

    return WaiverRosterPlayersResponse(
        league_id=league.league_id,
        league_name=league.name,
        roster_id=roster.roster_id,

        value_basis=value_basis,
        value_label=get_value_label(
            value_basis,
            war_value_settings,
        ),

        total_players=len(roster_players),
        players=roster_players,
    )
