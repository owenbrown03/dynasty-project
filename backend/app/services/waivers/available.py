from __future__ import annotations

from collections.abc import Iterable

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.war.dynasty.factory import (
    build_dynasty_war_service,
)
from app.analytics.war.redraft.models import PlayerWAR
from app.analytics.war.redraft.service import WARService
from app.analytics.war.dynasty.models import DynastyProjection
from app.crud.value import get_player_values
from app.infrastructure.redis.client import RedisClient
from app.models.db.sleeper.api import League, Roster
from app.models.db.sleeper.connection import SleeperConnection
from app.schemas.waivers import (
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
from app.services.waivers.dynasty import (
    DYNASTY_FANTASY_POSITIONS,
    build_dynasty_projection,
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

    roster_capacity = (
        league.roster_size
        + league.taxi_slots
        + league.reserve_slots
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

    result = await db.execute(
        select(Roster, League)
        .join(
            League,
            League.league_id == Roster.league_id,
        )
        .where(
            Roster.owner_id == connection.sleeper_user_id,
        )
        .order_by(League.name)
    )

    return [
        build_league_option(
            roster=roster,
            league=league,
        )
        for roster, league in result.all()
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


def project_full_available_dynasty_pool(
    *,
    available_war_players: Iterable[PlayerWAR],
) -> dict[str, DynastyProjection]:
    """
    Option A: calculate dynasty WAR for every available supported player
    in the selected league.

    This is intentionally complete, not candidate-limited, so sorting by
    dynasty WAR in the detailed table is accurate.
    """

    dynasty_service = build_dynasty_war_service()

    dynasty_by_player_id: dict[str, DynastyProjection] = {}

    for player_war in available_war_players:
        projection = build_dynasty_projection(
            player_war=player_war,
            dynasty_service=dynasty_service,
        )

        if projection is not None:
            dynasty_by_player_id[
                player_war.player_id
            ] = projection

    return dynasty_by_player_id


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


async def get_available_waiver_players(
    *,
    db: AsyncSession,
    redis: RedisClient,
    connection: SleeperConnection,
    league_id: str,
    value_basis: ValueBasis,
    war_service: WARService,
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

    roster, league = await get_owned_waiver_league(
        db=db,
        connection=connection,
        league_id=league_id,
    )

    rostered_player_ids = await get_rostered_player_ids(
        db=db,
        league_id=league_id,
    )

    redraft_war_players = await war_service.calculate(
        db=db,
        redis=redis,
        league_id=league_id,
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
        project_full_available_dynasty_pool(
            available_war_players=available_war_players,
        )
    )

    player_values = await get_player_values(
        db=db,
        player_ids=available_player_ids,
        redraft_war_players=redraft_war_players,
        dynasty_war_by_player_id=dynasty_war_by_player_id,
    )

    available_players: list[WaiverAvailablePlayer] = []

    for player in player_values:
        selected_value = get_player_value(
            player=player,
            basis=value_basis,
        )

        available_players.append(
            WaiverAvailablePlayer(
                **player.model_dump(),
                selected_value=selected_value,
            )
        )

    sorted_players = sort_available_players(
        players=available_players,
    )

    return WaiverAvailablePlayersResponse(
        league_id=league.league_id,
        league_name=league.name,
        league_avatar=league.avatar,

        roster_id=roster.roster_id,

        value_basis=value_basis,
        value_label=get_value_label(value_basis),

        total_players=len(sorted_players),
        players=sorted_players,
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
        project_full_available_dynasty_pool(
            available_war_players=roster_war_players,
        )
    )

    player_values = await get_player_values(
        db=db,
        player_ids=roster_player_ids,
        redraft_war_players=redraft_war_players,
        dynasty_war_by_player_id=dynasty_war_by_player_id,
    )

    roster_players: list[WaiverRosterPlayer] = []

    for player in player_values:
        selected_value = get_player_value(
            player=player,
            basis=value_basis,
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
        value_label=get_value_label(value_basis),

        total_players=len(roster_players),
        players=roster_players,
    )