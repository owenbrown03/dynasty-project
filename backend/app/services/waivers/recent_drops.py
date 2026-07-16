from __future__ import annotations

from collections import defaultdict

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.war.dynasty.models import DynastyProjection
from app.analytics.war.redraft.models import PlayerWAR
from app.analytics.war.redraft.service import WARService
from app.crud.auth.user import get_war_value_settings_by_user_id
from app.crud.sleeper.league import (
    get_sync_states,
    needs_recent_activity_sync,
    sync_transactions_for_known_leagues,
)
from app.crud.value import get_player_values
from app.infrastructure.redis.client import RedisClient
from app.models.db.sleeper.api import League, Movement, Player, Roster, Transaction
from app.models.db.sleeper.connection import SleeperConnection
from app.schemas.waivers import (
    WaiverRecentlyDroppedPlayer,
    WaiverRecentlyDroppedResponse,
)
from app.services.leagues.selection import get_visible_owned_league_rows_by_sleeper_user_id
from app.services.personal_values import hydrate_personal_player_values
from app.services.war.shared import (
    build_shared_redraft_war_by_league_id,
)
from app.services.values.basis import (
    ValueBasis,
    get_player_value,
    get_value_label,
)
from app.services.waivers.available import project_full_available_dynasty_pool
from app.services.waivers.bulk import get_rostered_player_ids_by_league
from app.services.waivers.claims import get_claim_block_reason


MAX_RECENT_DROPS = 200
SUPPORTED_POSITIONS = {
    "QB",
    "RB",
    "WR",
    "TE",
}
RECENT_DROP_TRANSACTION_TYPES = {
    "waiver",
    "free_agent",
    "commissioner",
}


def needs_recent_drops_sync(
    *,
    sync_states: dict[str, object],
    league_ids: list[str],
) -> bool:
    return any(
        needs_recent_activity_sync(
            sync_states.get(league_id),
        )
        for league_id in league_ids
    )


async def get_recent_drops_sync_required(
    *,
    db: AsyncSession,
    connection: SleeperConnection,
) -> bool:
    if not connection.sleeper_user_id:
        return False

    visible_rows = await get_visible_owned_league_rows_by_sleeper_user_id(
        db=db,
        sleeper_user_id=connection.sleeper_user_id,
        site_user_id=connection.site_user_id,
    )

    league_ids = [
        row.league.league_id
        for row in visible_rows
    ]

    if not league_ids:
        return False

    sync_states = await get_sync_states(
        db,
        league_ids,
    )

    return needs_recent_drops_sync(
        sync_states=sync_states,
        league_ids=league_ids,
    )


async def get_recently_dropped_players(
    *,
    db: AsyncSession,
    redis: RedisClient,
    connection: SleeperConnection,
    value_basis: ValueBasis,
    war_service: WARService,
    sync_requested: bool = False,
) -> WaiverRecentlyDroppedResponse:
    if not connection.sleeper_user_id:
        return WaiverRecentlyDroppedResponse(
            sleeper_username=connection.sleeper_username,
            value_basis=value_basis,
            value_label=get_value_label(
                value_basis,
                None,
            ),
            sync_requested=sync_requested,
            total_players=0,
            players=[],
        )

    visible_rows = await get_visible_owned_league_rows_by_sleeper_user_id(
        db=db,
        sleeper_user_id=connection.sleeper_user_id,
        site_user_id=connection.site_user_id,
    )

    if not visible_rows:
        return WaiverRecentlyDroppedResponse(
            sleeper_username=connection.sleeper_username,
            value_basis=value_basis,
            value_label=get_value_label(
                value_basis,
                None,
            ),
            sync_requested=sync_requested,
            total_players=0,
            players=[],
        )

    league_by_id: dict[str, League] = {
        row.league.league_id: row.league
        for row in visible_rows
    }
    roster_by_league_id: dict[str, Roster] = {
        row.league.league_id: row.roster
        for row in visible_rows
    }
    league_ids = list(
        league_by_id.keys(),
    )

    rostered_by_league = await get_rostered_player_ids_by_league(
        db=db,
        league_ids=league_ids,
    )

    drop_result = await db.execute(
        select(
            Transaction.transaction_id,
            Transaction.time_ms,
            Transaction.league_id,
            Movement.player_id,
            Player,
        )
        .join(
            Movement,
            Movement.transaction_id == Transaction.transaction_id,
        )
        .join(
            Player,
            Player.player_id == Movement.player_id,
        )
        .where(
            Transaction.league_id.in_(league_ids),
            Movement.action == "DROP",
            or_(
                Transaction.status == "complete",
                Transaction.status.is_(None),
            ),
            Transaction.type.in_(RECENT_DROP_TRANSACTION_TYPES),
            Movement.player_id.is_not(None),
        )
        .order_by(
            Transaction.time_ms.desc(),
        )
        .limit(MAX_RECENT_DROPS)
    )

    drop_rows = drop_result.all()

    league_drop_rows: dict[str, list[tuple[str, int, Player]]] = defaultdict(list)

    for transaction_id, time_ms, league_id, player_id, player in drop_rows:
        if (
            not player_id
            or player is None
            or player.position not in SUPPORTED_POSITIONS
        ):
            continue

        if player_id in rostered_by_league.get(
            league_id,
            set(),
        ):
            continue

        league_drop_rows[league_id].append(
            (
                transaction_id,
                time_ms,
                player,
            )
        )

    war_value_settings = await get_war_value_settings_by_user_id(
        db=db,
        site_user_id=connection.site_user_id,
    )
    value_label = get_value_label(
        value_basis,
        war_value_settings,
    )

    selected_value_by_key: dict[tuple[str, str], float | None] = {}
    player_value_by_key: dict[tuple[str, str], object] = {}
    redraft_war_by_league_id = (
        await build_shared_redraft_war_by_league_id(
            db=db,
            leagues=list(
                league_by_id.values()
            ),
            war_service=war_service,
        )
    )

    for league_id, entries in league_drop_rows.items():
        league = league_by_id.get(
            league_id,
        )

        if league is None:
            continue

        redraft_war_players = redraft_war_by_league_id[
            league_id
        ]

        redraft_by_player_id = {
            player.player_id: player
            for player in redraft_war_players
        }

        league_war_players: list[PlayerWAR] = [
            redraft_by_player_id[player.player_id]
            for _, _, player in entries
            if player.player_id in redraft_by_player_id
        ]

        if not league_war_players:
            continue

        dynasty_by_player_id: dict[str, DynastyProjection] = (
            await project_full_available_dynasty_pool(
                redis=redis,
                available_war_players=league_war_players,
            )
        )

        player_ids = [
            player.player_id
            for player in league_war_players
        ]

        player_values = await get_player_values(
            db=db,
            player_ids=player_ids,
            redraft_war_players=redraft_war_players,
            dynasty_war_by_player_id=dynasty_by_player_id,
        )

        if value_basis == ValueBasis.MY_WAR:
            player_values = await hydrate_personal_player_values(
                db=db,
                site_user_id=connection.site_user_id,
                league=league,
                player_values=player_values,
                redis=redis,
            )

        for player_value in player_values:
            key = (
                league_id,
                player_value.player_id,
            )
            player_value_by_key[key] = player_value
            selected_value_by_key[key] = get_player_value(
                player=player_value,
                basis=value_basis,
                war_value_settings=war_value_settings,
            )

    players: list[WaiverRecentlyDroppedPlayer] = []

    for transaction_id, time_ms, league_id, _, player in drop_rows:
        league = league_by_id.get(
            league_id,
        )
        roster = roster_by_league_id.get(
            league_id,
        )

        if league is None or roster is None or player is None:
            continue

        key = (
            league_id,
            player.player_id,
        )
        player_value = player_value_by_key.get(
            key,
        )

        if player_value is None:
            continue

        faab_remaining = roster.faab_remaining(
            league,
        )
        faab_percent_remaining = 0.0

        if league.waiver_budget > 0:
            faab_percent_remaining = round(
                (faab_remaining / league.waiver_budget) * 100,
                1,
            )

        claim_blocked_reason = get_claim_block_reason(
            roster=roster,
            league=league,
        )

        players.append(
            WaiverRecentlyDroppedPlayer(
                **player_value.model_dump(),
                transaction_id=transaction_id,
                dropped_at_ms=time_ms,
                league_id=league_id,
                league_name=league.name,
                league_avatar=league.avatar,
                roster_id=roster.roster_id,
                roster_spots_available=roster.open_roster_spots(
                    league,
                ),
                faab_remaining=faab_remaining,
                faab_percent_remaining=faab_percent_remaining,
                can_submit_claim=claim_blocked_reason is None,
                claim_blocked_reason=claim_blocked_reason,
                selected_value=selected_value_by_key.get(
                    key,
                ),
            )
        )

    return WaiverRecentlyDroppedResponse(
        sleeper_username=connection.sleeper_username,
        value_basis=value_basis,
        value_label=value_label,
        sync_requested=sync_requested,
        total_players=len(players),
        players=players,
    )


async def sync_recent_drop_activity(
    *,
    db: AsyncSession,
    sleeper,
    connection: SleeperConnection,
) -> bool:
    if not connection.sleeper_user_id:
        return False

    visible_rows = await get_visible_owned_league_rows_by_sleeper_user_id(
        db=db,
        sleeper_user_id=connection.sleeper_user_id,
        site_user_id=connection.site_user_id,
    )

    leagues = [
        row.league
        for row in visible_rows
    ]

    if not leagues:
        return False

    sync_states = await get_sync_states(
        db,
        [
            league.league_id
            for league in leagues
        ],
    )

    leagues_to_sync = [
        league
        for league in leagues
        if needs_recent_activity_sync(
            sync_states.get(league.league_id),
        )
    ]

    if not leagues_to_sync:
        return False

    state = await sleeper.read.get_nfl_state()
    curr_week = max(
        int(state.week),
        1,
    )

    await sync_transactions_for_known_leagues(
        db=db,
        leagues=leagues_to_sync,
        curr_week=curr_week,
        sleeper=sleeper,
    )

    return True
