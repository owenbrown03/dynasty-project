from __future__ import annotations

import logging
from collections import defaultdict

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.sleeper.exceptions import (
    SleeperGraphQLError,
)
from app.analytics.war.dynasty.factory import (
    build_dynasty_war_service,
)
from app.analytics.war.dynasty.models import DynastyProjection
from app.analytics.war.redraft.models import PlayerWAR
from app.analytics.war.redraft.service import WARService
from app.crud.value import get_player_values
from app.infrastructure.redis.client import RedisClient
from app.integrations.sleeper.client import SleeperClient
from app.models.db.fc.models import FantasyCalcValue
from app.models.db.ktc.models import KTCValue
from app.models.db.sleeper.api import League, Player, Roster
from app.models.db.sleeper.connection import SleeperConnection
from app.models.db.underdog.models import UnderdogADP
from app.schemas.player import PlayerValue
from app.schemas.waivers import (
    BulkWaiverAvailabilityResponse,
    BulkWaiverClaimRequest,
    BulkWaiverClaimResponse,
    BulkWaiverClaimResult,
    BulkWaiverLeagueAvailability,
    BulkWaiverPlayerSearchResult,
)
from app.services.values.basis import (
    ValueBasis,
    get_player_value,
    get_value_label,
)
from app.services.waivers.claims import (
    get_claim_block_reason,
    submit_claim,
)
from app.services.waivers.dynasty import (
    DYNASTY_FANTASY_POSITIONS,
    build_dynasty_projection,
)
from app.crud.sleeper.player import get_bulk_target_player
from app.crud.sleeper.roster import get_owned_roster_rows
from app.utils.age import calculate_age


logger = logging.getLogger(__name__)


DYNASTY_VALUE_BASES = {
    ValueBasis.DYNASTY_STARTER_WAR,
    ValueBasis.DYNASTY_ROSTER_WAR,
}


async def search_bulk_waiver_players(
    *,
    db: AsyncSession,
    query: str,
    limit: int = 10,
) -> list[BulkWaiverPlayerSearchResult]:
    """
    Searches only players already stored in our local Sleeper player table.

    The frontend receives the local Sleeper player_id from this result and
    uses that ID for the later cross-league availability request.
    """

    search_term = query.strip()

    if len(search_term) < 2:
        return []

    player_name_expression = func.concat_ws(
        " ",
        Player.first_name,
        Player.last_name,
    )

    result = await db.execute(
        select(Player)
        .where(
            Player.position.in_(DYNASTY_FANTASY_POSITIONS),
            player_name_expression.ilike(
                f"%{search_term}%",
            ),
        )
        .order_by(
            Player.last_name,
            Player.first_name,
        )
        .limit(limit)
    )

    players = list(
        result.scalars(),
    )

    if not players:
        return []

    player_ids = [
        player.player_id
        for player in players
    ]

    ktc_result = await db.execute(
        select(KTCValue).where(
            KTCValue.player_id.in_(player_ids),
        )
    )

    ktc_by_player_id = {
        value.player_id: value
        for value in ktc_result.scalars()
    }

    fc_result = await db.execute(
        select(FantasyCalcValue).where(
            FantasyCalcValue.player_id.in_(player_ids),
        )
    )

    fc_by_player_id = {
        value.player_id: value
        for value in fc_result.scalars()
    }

    underdog_result = await db.execute(
        select(UnderdogADP)
        .where(
            UnderdogADP.player_id.in_(player_ids),
        )
        .order_by(
            UnderdogADP.player_id,
            UnderdogADP.id.desc(),
        )
    )

    underdog_by_player_id: dict[str, UnderdogADP] = {}

    for row in underdog_result.scalars():
        if row.player_id not in underdog_by_player_id:
            underdog_by_player_id[
                row.player_id
            ] = row

    return [
        BulkWaiverPlayerSearchResult(
            player_id=player.player_id,
            name=player.full_name,
            position=player.position,
            team=player.team,
            age=calculate_age(
                player.birth_date,
            ),

            ktc_value=(
                ktc_by_player_id[
                    player.player_id
                ].sf_value
                if player.player_id in ktc_by_player_id
                else None
            ),

            fc_value=(
                fc_by_player_id[
                    player.player_id
                ].value
                if player.player_id in fc_by_player_id
                else None
            ),

            underdog_position_rank=(
                underdog_by_player_id[
                    player.player_id
                ].position_rank
                if player.player_id in underdog_by_player_id
                else None
            ),
        )
        for player in players
    ]


async def get_rostered_player_ids_by_league(
    *,
    db: AsyncSession,
    league_ids: list[str],
) -> dict[str, set[str]]:
    """
    Returns all rostered player IDs for every selected league.
    """

    result = await db.execute(
        select(
            Roster.league_id,
            Roster.players,
        )
        .where(
            Roster.league_id.in_(league_ids),
        )
    )

    rostered_by_league: dict[
        str,
        set[str],
    ] = defaultdict(set)

    for league_id, player_ids in result.all():
        rostered_by_league[league_id].update(
            player_id
            for player_id in (player_ids or [])
            if player_id
        )

    return rostered_by_league


def get_recommended_drop_ids(
    *,
    roster: Roster,
    war_by_player_id: dict[str, PlayerWAR],
) -> list[str]:
    """
    Prefer non-starters as drop recommendations.

    If every eligible player is currently in a starter slot, fall back
    to the user's full QB/RB/WR/TE roster.
    """

    supported_roster_player_ids = [
        player_id
        for player_id in (roster.players or [])
        if (
            player_id in war_by_player_id
            and war_by_player_id[
                player_id
            ].position in DYNASTY_FANTASY_POSITIONS
        )
    ]

    starter_ids = set(
        roster.starters or [],
    )

    non_starter_player_ids = [
        player_id
        for player_id in supported_roster_player_ids
        if player_id not in starter_ids
    ]

    return (
        non_starter_player_ids
        or supported_roster_player_ids
    )


def build_selected_dynasty_values(
    *,
    player_war_results: list[PlayerWAR],
    player_ids: set[str],
) -> dict[str, DynastyProjection]:
    """
    Projects dynasty WAR only for the bulk target player and the
    potential drop candidates in one league.

    Unlike the detailed available-player table, this does not need to
    dynasty-project the entire waiver pool.
    """

    dynasty_service = build_dynasty_war_service()

    war_by_player_id = {
        player.player_id: player
        for player in player_war_results
    }

    dynasty_by_player_id: dict[
        str,
        DynastyProjection,
    ] = {}

    for player_id in player_ids:
        player_war = war_by_player_id.get(
            player_id,
        )

        if player_war is None:
            continue

        projection = build_dynasty_projection(
            player_war=player_war,
            dynasty_service=dynasty_service,
        )

        if projection is not None:
            dynasty_by_player_id[
                player_id
            ] = projection

    return dynasty_by_player_id


async def build_bulk_league_availability(
    *,
    db: AsyncSession,
    redis: RedisClient,
    roster: Roster,
    league: League,
    target_player: Player,
    rostered_player_ids: set[str],
    value_basis: ValueBasis,
    war_service: WARService,
) -> BulkWaiverLeagueAvailability:
    """
    Builds one bulk-claim row for a single owned league.
    """

    target_player_id = target_player.player_id

    already_rostered_by_you = (
        target_player_id in set(
            roster.players or [],
        )
    )

    is_available = (
        target_player_id
        not in rostered_player_ids
    )

    faab_remaining = roster.faab_remaining(
        league,
    )

    roster_spots_available = (
        roster.open_roster_spots(
            league,
        )
    )

    requires_drop = (
        roster_spots_available == 0
    )

    claim_blocked_reason = get_claim_block_reason(
        roster=roster,
        league=league,
    )

    can_submit_claim = (
        is_available
        and claim_blocked_reason is None
    )

    if not is_available:
        return BulkWaiverLeagueAvailability(
            league_id=league.league_id,
            league_name=league.name,
            league_avatar=league.avatar,

            roster_id=roster.roster_id,

            is_available=False,
            already_rostered_by_you=(
                already_rostered_by_you
            ),
            unavailable_reason=(
                "Already on your roster"
                if already_rostered_by_you
                else "Rostered in this league"
            ),

            can_submit_claim=False,
            claim_blocked_reason=None,

            faab_remaining=faab_remaining,
            roster_spots_available=(
                roster_spots_available
            ),
            requires_drop=requires_drop,
        )

    redraft_war_players = await war_service.calculate(
        db=db,
        redis=redis,
        league_id=league.league_id,
    )

    war_by_player_id = {
        player.player_id: player
        for player in redraft_war_players
    }

    recommended_drop_ids = get_recommended_drop_ids(
        roster=roster,
        war_by_player_id=war_by_player_id,
    )

    relevant_player_ids = list(
        dict.fromkeys(
            [
                target_player_id,
                *recommended_drop_ids,
            ]
        )
    )

    dynasty_war_by_player_id: dict[
        str,
        DynastyProjection,
    ] = {}

    if value_basis in DYNASTY_VALUE_BASES:
        dynasty_war_by_player_id = (
            build_selected_dynasty_values(
                player_war_results=redraft_war_players,
                player_ids=set(
                    relevant_player_ids,
                ),
            )
        )

    player_values = await get_player_values(
        db=db,
        player_ids=relevant_player_ids,
        redraft_war_players=redraft_war_players,
        dynasty_war_by_player_id=(
            dynasty_war_by_player_id
        ),
    )

    value_by_player_id = {
        player.player_id: player
        for player in player_values
    }

    add_player_value = value_by_player_id.get(
        target_player_id,
    )

    add_selected_value = (
        get_player_value(
            player=add_player_value,
            basis=value_basis,
        )
        if add_player_value is not None
        else None
    )

    drop_candidates: list[
        tuple[PlayerValue, float]
    ] = []

    for player_id in recommended_drop_ids:
        player = value_by_player_id.get(
            player_id,
        )

        if player is None:
            continue

        selected_value = get_player_value(
            player=player,
            basis=value_basis,
        )

        if selected_value is None:
            continue

        drop_candidates.append(
            (
                player,
                selected_value,
            )
        )

    recommended_drop: PlayerValue | None = None
    recommended_drop_selected_value: float | None = None

    if drop_candidates:
        (
            recommended_drop,
            recommended_drop_selected_value,
        ) = min(
            drop_candidates,
            key=lambda item: item[1],
        )

    return BulkWaiverLeagueAvailability(
        league_id=league.league_id,
        league_name=league.name,
        league_avatar=league.avatar,

        roster_id=roster.roster_id,

        is_available=True,

        can_submit_claim=can_submit_claim,
        claim_blocked_reason=claim_blocked_reason,

        faab_remaining=faab_remaining,
        roster_spots_available=roster_spots_available,
        requires_drop=requires_drop,

        add_selected_value=add_selected_value,

        recommended_drop=recommended_drop,
        recommended_drop_selected_value=(
            recommended_drop_selected_value
        ),
    )


async def get_bulk_waiver_availability(
    *,
    db: AsyncSession,
    redis: RedisClient,
    connection: SleeperConnection,
    player_id: str,
    value_basis: ValueBasis,
    war_service: WARService,
) -> BulkWaiverAvailabilityResponse:
    """
    Checks one target player across every league owned by the connected user.
    """

    target_player = await get_bulk_target_player(
        db=db,
        player_id=player_id,
    )

    owned_roster_rows = await get_owned_roster_rows(
        db=db,
        connection=connection,
    )

    league_ids = [
        league.league_id
        for _, league in owned_roster_rows
    ]

    rostered_by_league = (
        await get_rostered_player_ids_by_league(
            db=db,
            league_ids=league_ids,
        )
    )

    league_availability: list[
        BulkWaiverLeagueAvailability
    ] = []

    for roster, league in owned_roster_rows:
        availability = (
            await build_bulk_league_availability(
                db=db,
                redis=redis,
                roster=roster,
                league=league,
                target_player=target_player,
                rostered_player_ids=(
                    rostered_by_league[
                        league.league_id
                    ]
                ),
                value_basis=value_basis,
                war_service=war_service,
            )
        )

        league_availability.append(
            availability,
        )

    return BulkWaiverAvailabilityResponse(
        player=BulkWaiverPlayerSearchResult(
            player_id=target_player.player_id,
            name=target_player.full_name,
            position=target_player.position,
            team=target_player.team,
            age=calculate_age(
                target_player.birth_date,
            ),
        ),

        value_basis=value_basis,
        value_label=get_value_label(
            value_basis,
        ),

        leagues=league_availability,
    )


def validate_bulk_claim_request(
    *,
    request: BulkWaiverClaimRequest,
) -> None:
    """
    A target player can have one claim per owned league in this bulk flow.
    """

    seen_leagues: set[str] = set()

    for claim in request.claims:
        if claim.league_id in seen_leagues:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Bulk claims may contain only one claim "
                    "per league."
                ),
            )

        seen_leagues.add(
            claim.league_id,
        )


async def submit_bulk_claims(
    *,
    db: AsyncSession,
    connection: SleeperConnection | None,
    sleeper: SleeperClient,
    request: BulkWaiverClaimRequest,
) -> BulkWaiverClaimResponse:
    """
    Submits claims one league at a time.

    Sleeper does not provide a cross-league atomic bulk claim mutation,
    so this intentionally returns a success/error result for each league.
    """

    validate_bulk_claim_request(
        request=request,
    )

    results: list[
        BulkWaiverClaimResult
    ] = []

    for claim in request.claims:
        try:
            response = await submit_claim(
                db=db,
                connection=connection,
                sleeper=sleeper,
                claim=claim,
            )

            results.append(
                BulkWaiverClaimResult(
                    league_id=claim.league_id,
                    roster_id=claim.roster_id,

                    success=True,

                    transaction_id=(
                        response.transaction_id
                    ),
                )
            )

        except HTTPException as exc:
            results.append(
                BulkWaiverClaimResult(
                    league_id=claim.league_id,
                    roster_id=claim.roster_id,

                    success=False,

                    error=str(exc.detail),
                )
            )

        except SleeperGraphQLError as exc:
            logger.warning(
                "Sleeper rejected bulk waiver claim "
                "league=%s roster=%s error=%s",
                claim.league_id,
                claim.roster_id,
                exc,
            )

            results.append(
                BulkWaiverClaimResult(
                    league_id=claim.league_id,
                    roster_id=claim.roster_id,

                    success=False,

                    error=str(exc),
                )
            )

        except Exception:
            logger.exception(
                "Bulk waiver claim failed for league=%s roster=%s",
                claim.league_id,
                claim.roster_id,
            )

            results.append(
                BulkWaiverClaimResult(
                    league_id=claim.league_id,
                    roster_id=claim.roster_id,

                    success=False,

                    error=(
                        "Unexpected error while submitting "
                        "this Sleeper waiver claim."
                    ),
                )
            )

    return BulkWaiverClaimResponse(
        results=results,
    )