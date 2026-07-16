from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.war.dynasty.factory import (
    build_dynasty_war_service,
)
from app.crud.auth.user import get_war_value_settings_by_user_id
from app.analytics.war.redraft.service import WARService
from app.crud.value import get_player_values
from app.infrastructure.redis.client import RedisClient
from app.models.db.sleeper.api import League, Roster
from app.models.db.sleeper.connection import SleeperConnection
from app.schemas.player import PlayerValue
from app.schemas.waivers import (
    WaiverLeagueOverview,
    WaiverOverviewResponse,
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
    build_shared_redraft_war_by_league_id,
)
from app.services.waivers.dynasty import (
    DYNASTY_FANTASY_POSITIONS,
    project_players_for_waivers,
)
from .constants import WAIVER_CANDIDATE_LIMIT


def get_best_available_player(
    available_players: list[PlayerValue],
    value_basis: ValueBasis,
    war_value_settings=None,
) -> tuple[PlayerValue | None, float | None]:
    candidates = [
        (
            player,
            get_player_value(
                player=player,
                basis=value_basis,
                war_value_settings=war_value_settings,
            ),
        )
        for player in available_players
    ]

    candidates = [
        (player, value)
        for player, value in candidates
        if value is not None
    ]

    if not candidates:
        return None, None

    return max(
        candidates,
        key=lambda item: item[1],
    )


def get_suggested_drop(
    roster_players: list[PlayerValue],
    value_basis: ValueBasis,
    war_value_settings=None,
) -> tuple[PlayerValue | None, float | None]:
    candidates = [
        (
            player,
            get_player_value(
                player=player,
                basis=value_basis,
                war_value_settings=war_value_settings,
            ),
        )
        for player in roster_players
    ]

    candidates = [
        (player, value)
        for player, value in candidates
        if value is not None
    ]

    if not candidates:
        return None, None

    return min(
        candidates,
        key=lambda item: item[1],
    )


async def get_waiver_overview(
    *,
    db: AsyncSession,
    redis: RedisClient,
    connection: SleeperConnection,
    war_service: WARService,
    value_basis: ValueBasis,
) -> WaiverOverviewResponse:
    """
    Builds one waiver overview card for every league owned by the
    connected Sleeper account.

    Recommendation basis for this version:
    - suggested add: highest dynasty roster WAR among available players
    - suggested drop: lowest dynasty roster WAR among non-starters
    - gain: add dynasty roster WAR minus drop dynasty roster WAR
    """

    if not connection.sleeper_user_id:
        return WaiverOverviewResponse(
            sleeper_username=connection.sleeper_username,
        )

    owned_rows = await get_visible_owned_league_rows_by_sleeper_user_id(
        db=db,
        sleeper_user_id=connection.sleeper_user_id,
        site_user_id=connection.site_user_id,
    )
    owned_roster_rows = [
        (row.roster, row.league)
        for row in owned_rows
    ]

    if not owned_roster_rows:
        return WaiverOverviewResponse(
            sleeper_username=connection.sleeper_username,
        )

    league_ids = [
        league.league_id
        for _, league in owned_roster_rows
    ]

    all_rosters_stmt = select(
        Roster.league_id,
        Roster.players,
    ).where(
        Roster.league_id.in_(league_ids),
    )

    all_rosters_result = await db.execute(
        all_rosters_stmt
    )

    rostered_player_ids_by_league: dict[
        str,
        set[str],
    ] = defaultdict(set)

    for league_id, player_ids in all_rosters_result.all():
        rostered_player_ids_by_league[league_id].update(
            player_id
            for player_id in (player_ids or [])
            if player_id
        )

    dynasty_war_service = build_dynasty_war_service()
    war_value_settings = await get_war_value_settings_by_user_id(
        db=db,
        site_user_id=connection.site_user_id,
    )

    overview_cards: list[WaiverLeagueOverview] = []
    redraft_war_by_league_id = (
        await build_shared_redraft_war_by_league_id(
            db=db,
            leagues=[
                league
                for _, league in owned_roster_rows
            ],
            war_service=war_service,
        )
    )

    for roster, league in owned_roster_rows:
        redraft_war_players = redraft_war_by_league_id[
            league.league_id
        ]

        redraft_war_by_player_id = {
            player.player_id: player
            for player in redraft_war_players
        }

        rostered_player_ids = rostered_player_ids_by_league[
            league.league_id
        ]

        user_roster_player_ids = {
            player_id
            for player_id in (roster.players or [])
            if (
                player_id in redraft_war_by_player_id
                and redraft_war_by_player_id[player_id].position
                in DYNASTY_FANTASY_POSITIONS
            )
        }

        available_player_ids = {
            player.player_id
            for player in redraft_war_players
            if (
                player.player_id not in rostered_player_ids
                and player.position in DYNASTY_FANTASY_POSITIONS
            )
        }

        dynasty_war_by_player_id = (
            project_players_for_waivers(
                player_war_results=redraft_war_players,
                available_player_ids=available_player_ids,
                user_roster_player_ids=user_roster_player_ids,
                dynasty_service=dynasty_war_service,
            )
        )

        top_available_player_ids = [
            player.player_id
            for player in redraft_war_players
            if (
                player.player_id in available_player_ids
                and player.player_id
                in dynasty_war_by_player_id
            )
        ][:WAIVER_CANDIDATE_LIMIT]

        starter_ids = set(roster.starters or [])

        non_starter_player_ids = [
            player_id
            for player_id in user_roster_player_ids
            if player_id not in starter_ids
        ]

        if not non_starter_player_ids:
            non_starter_player_ids = list(
                user_roster_player_ids
            )

        relevant_player_ids = list(
            dict.fromkeys(
                top_available_player_ids
                + non_starter_player_ids
            )
        )

        enriched_values = await get_player_values(
            db=db,
            player_ids=relevant_player_ids,
            redraft_war_players=redraft_war_players,
            dynasty_war_by_player_id=dynasty_war_by_player_id,
        )
        if value_basis == ValueBasis.MY_WAR:
            enriched_values = await hydrate_personal_player_values(
                db=db,
                site_user_id=connection.site_user_id,
                league=league,
                player_values=enriched_values,
            )

        enriched_by_player_id = {
            player.player_id: player
            for player in enriched_values
        }

        available_values = [
            enriched_by_player_id[player_id]
            for player_id in top_available_player_ids
            if player_id in enriched_by_player_id
        ]

        drop_candidate_values = [
            enriched_by_player_id[player_id]
            for player_id in non_starter_player_ids
            if player_id in enriched_by_player_id
        ]

        suggested_add, suggested_add_value = (
            get_best_available_player(
                available_players=available_values,
                value_basis=value_basis,
                war_value_settings=war_value_settings,
            )
        )

        suggested_drop, suggested_drop_value = (
            get_suggested_drop(
                roster_players=drop_candidate_values,
                value_basis=value_basis,
                war_value_settings=war_value_settings,
            )
        )

        value_gain: float | None = None

        if (
            suggested_add_value is not None
            and suggested_drop_value is not None
        ):
            value_gain = round(
                suggested_add_value - suggested_drop_value,
                3,
            )

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

        overview_cards.append(
            WaiverLeagueOverview(
                league_id=league.league_id,
                league_name=league.name,
                league_avatar=league.avatar,

                roster_id=roster.roster_id,

                roster_size=roster.roster_size,
                roster_capacity=roster_capacity,
                roster_spots_available=(
                    roster.open_roster_spots(league)
                ),

                faab_budget=faab_budget,
                faab_used=roster.waiver_budget_used,
                faab_remaining=faab_remaining,
                faab_percent_remaining=(
                    faab_percent_remaining
                ),

                available_player_count=len(
                    available_player_ids
                ),

                value_basis=value_basis,
                value_label=get_value_label(
                    value_basis,
                    war_value_settings,
                ),

                suggested_add=suggested_add,
                suggested_drop=suggested_drop,

                suggested_add_value=suggested_add_value,
                suggested_drop_value=suggested_drop_value,
                value_gain=value_gain,

                can_submit_claim=bool(
                    connection.encrypted_token
                ),
            )
        )

    return WaiverOverviewResponse(
        sleeper_username=connection.sleeper_username,
        leagues=overview_cards,
    )
