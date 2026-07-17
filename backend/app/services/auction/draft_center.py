from __future__ import annotations

import asyncio
from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.analytics.war.redraft.service import WARService
from app.crud.auth.user import get_war_value_settings_by_user_id
from app.crud.value import get_player_values
from app.infrastructure.redis.client import RedisClient
from app.models.db.sleeper import api as sleeper_model
from app.models.db.sleeper.api import Player
from app.models.db.sleeper.connection import SleeperConnection
from app.schemas.auction import (
    AuctionAvailablePlayerAsset,
    AuctionDraftMyTeam,
    AuctionDraftPlayerAsset,
    AuctionDraftPositionSummary,
    AuctionDraftResponse,
    AuctionDraftTeamSummary,
)
from app.services.leagues.details import (
    LeagueDetails,
    build_cached_league_roster_construction_targets,
)
from app.services.personal_values import hydrate_personal_player_values
from app.services.sleeper import transformers
from app.services.values.basis import (
    ValueBasis,
    get_player_value,
    get_value_label,
)
from app.services.war.shared import (
    build_cached_dynasty_projections_by_player_id,
)
from app.services.waivers.dynasty import DYNASTY_FANTASY_POSITIONS


FALLBACK_AUCTION_BUDGET = 200


@dataclass(frozen=True)
class _DraftedPick:
    roster_id: int
    player_id: str
    amount_paid: int


def _extract_auction_budget(
    *,
    raw_draft: dict,
) -> int:
    settings = raw_draft.get("settings") or {}
    metadata = raw_draft.get("metadata") or {}

    for candidate in (
        settings.get("budget"),
        settings.get("auction_budget"),
        metadata.get("budget"),
        metadata.get("auction_budget"),
        raw_draft.get("budget"),
    ):
        try:
            if candidate is not None:
                return max(int(candidate), 1)
        except (TypeError, ValueError):
            continue

    return FALLBACK_AUCTION_BUDGET


def _extract_pick_amount(
    raw_pick: dict,
) -> int:
    metadata = raw_pick.get("metadata") or {}

    for candidate in (
        raw_pick.get("amount"),
        raw_pick.get("bid_amount"),
        metadata.get("amount"),
        metadata.get("bid_amount"),
    ):
        try:
            if candidate is not None:
                return max(int(candidate), 0)
        except (TypeError, ValueError):
            continue

    return 0


def _extract_drafted_picks(
    raw_picks: list[dict],
) -> list[_DraftedPick]:
    drafted: list[_DraftedPick] = []

    for raw_pick in raw_picks:
        if not isinstance(raw_pick, dict):
            continue

        player_id = raw_pick.get("player_id")
        roster_id = raw_pick.get("roster_id")

        if player_id is None or roster_id is None:
            continue

        try:
            drafted.append(
                _DraftedPick(
                    roster_id=int(roster_id),
                    player_id=str(player_id),
                    amount_paid=_extract_pick_amount(
                        raw_pick,
                    ),
                )
            )
        except (TypeError, ValueError):
            continue

    return drafted


def _get_owner_name_and_avatar(
    *,
    roster_id: int,
    roster_by_id: dict[int, sleeper_model.Roster],
    users_by_id: dict[str, object],
) -> tuple[str, str | None]:
    roster = roster_by_id.get(roster_id)

    if roster is None or not roster.owner_id:
        return f"Team {roster_id}", None

    user = users_by_id.get(roster.owner_id)

    if user is None:
        return f"Team {roster_id}", None

    display_name = getattr(
        user,
        "display_name",
        None,
    )
    avatar = getattr(
        user,
        "avatar",
        None,
    )

    return (
        str(display_name or f"Team {roster_id}"),
        str(avatar) if avatar else None,
    )


def _get_my_roster_id(
    *,
    connection: SleeperConnection,
    draft,
    rosters: list[sleeper_model.Roster],
) -> int | None:
    sleeper_user_id = connection.sleeper_user_id

    if not sleeper_user_id:
        return None

    slot = (draft.draft_order or {}).get(
        sleeper_user_id,
    )

    if slot is not None:
        roster_id = (draft.slot_to_roster_id or {}).get(
            str(slot),
        )
        if roster_id is not None:
            try:
                return int(roster_id)
            except (TypeError, ValueError):
                pass

    for roster in rosters:
        if roster.owner_id == sleeper_user_id:
            return int(roster.roster_id)

    return None


def _build_position_need_multipliers(
    *,
    roster_targets: list[AuctionDraftPositionSummary],
) -> dict[str, float]:
    multipliers: dict[str, float] = {}

    for summary in roster_targets:
        deficit = max(
            summary.target_count - summary.drafted_count,
            0,
        )
        target = max(summary.target_count, 1)
        multipliers[summary.position] = round(
            1.0 + (deficit / target),
            3,
        )

    return multipliers


def _build_position_summary_rows(
    *,
    targets_by_position: dict[str, int],
    drafted_assets: list[AuctionDraftPlayerAsset],
    budget: int,
) -> list[AuctionDraftPositionSummary]:
    drafted_count_by_position = {
        position: 0
        for position in DYNASTY_FANTASY_POSITIONS
    }
    spent_by_position = {
        position: 0
        for position in DYNASTY_FANTASY_POSITIONS
    }
    value_by_position = {
        position: 0.0
        for position in DYNASTY_FANTASY_POSITIONS
    }

    for asset in drafted_assets:
        position = asset.position

        if position not in drafted_count_by_position:
            continue

        drafted_count_by_position[position] += 1
        spent_by_position[position] += asset.amount_paid
        value_by_position[position] += float(
            asset.selected_value or 0.0,
        )

    return [
        AuctionDraftPositionSummary(
            position=position,
            target_count=int(
                targets_by_position.get(
                    position,
                    0,
                )
            ),
            drafted_count=drafted_count_by_position[
                position
            ],
            spent_amount=spent_by_position[position],
            spent_budget_pct=round(
                (
                    spent_by_position[position]
                    / max(budget, 1)
                ) * 100,
                1,
            ),
            selected_value_total=round(
                value_by_position[position],
                3,
            ),
        )
        for position in DYNASTY_FANTASY_POSITIONS
    ]


def _build_fair_market_prices(
    *,
    available_assets: list[tuple[object, float | None]],
    remaining_league_budget: int,
) -> dict[str, int]:
    positive_total = sum(
        max(value or 0.0, 0.0)
        for _, value in available_assets
    )

    if positive_total <= 0:
        return {
            getattr(player, "player_id"): 1
            for player, _ in available_assets
        }

    prices: dict[str, int] = {}

    for player, value in available_assets:
        player_id = getattr(
            player,
            "player_id",
        )
        positive_value = max(value or 0.0, 0.0)
        price = round(
            (positive_value / positive_total)
            * max(remaining_league_budget, 1),
        )
        prices[player_id] = max(price, 1)

    return prices


async def get_auction_draft_center(
    *,
    db: AsyncSession,
    redis: RedisClient | None,
    sleeper,
    connection: SleeperConnection,
    draft_id: str,
    value_basis: ValueBasis,
    search: str | None,
    page: int,
    page_size: int,
) -> AuctionDraftResponse:
    if not connection.sleeper_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Connect a Sleeper account before using "
                "the auction draft center."
            ),
        )

    raw_draft, raw_picks = await asyncio.gather(
        sleeper.transport.get(
            f"draft/{draft_id}",
        ),
        sleeper.read.get_draft_picks(
            draft_id,
        ),
    )

    if not isinstance(raw_draft, dict):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found.",
        )

    draft = sleeper.read.get_draft(
        draft_id,
    )

    draft_obj = await draft
    league_id = draft_obj.league_id
    league_schema, roster_schemas, user_schemas = await asyncio.gather(
        sleeper.read.get_league(
            league_id,
        ),
        sleeper.read.get_rosters(
            league_id,
        ),
        sleeper.read.get_users(
            league_id,
        ),
    )

    league = transformers.league_to_db(
        league_schema,
    )
    rosters = [
        transformers.roster_to_db(
            roster_schema,
        )
        for roster_schema in roster_schemas
    ]
    roster_by_id = {
        roster.roster_id: roster
        for roster in rosters
    }
    users_by_id = {
        user.user_id: user
        for user in user_schemas
    }

    my_roster_id = _get_my_roster_id(
        connection=connection,
        draft=draft_obj,
        rosters=rosters,
    )

    if my_roster_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "The connected Sleeper account does not appear "
                "to belong to this draft."
            ),
        )

    war_service = WARService()
    shared = await war_service.load_shared_data(
        db,
        int(league.season),
    )
    redraft_war_players = await war_service.calculate_with_shared_cache(
        redis=redis,
        league=league,
        shared=shared,
    )
    dynasty_by_player_id = (
        await build_cached_dynasty_projections_by_player_id(
            redis=redis,
            player_wars=redraft_war_players,
        )
    )

    eligible_player_rows = await db.execute(
        select(Player).where(
            Player.position.in_(
                list(
                    DYNASTY_FANTASY_POSITIONS,
                )
            ),
            Player.active == True,
        )
    )
    eligible_players = list(
        eligible_player_rows.scalars(),
    )
    eligible_player_ids = [
        player.player_id
        for player in eligible_players
    ]

    player_values = await get_player_values(
        db=db,
        player_ids=eligible_player_ids,
        redraft_war_players=redraft_war_players,
        dynasty_war_by_player_id=dynasty_by_player_id,
    )
    player_values = await hydrate_personal_player_values(
        db=db,
        site_user_id=connection.site_user_id,
        league=league,
        player_values=player_values,
        redis=redis,
    )
    player_value_by_id = {
        player.player_id: player
        for player in player_values
    }

    war_value_settings = await get_war_value_settings_by_user_id(
        db=db,
        site_user_id=connection.site_user_id,
    )
    value_label = get_value_label(
        value_basis,
        war_value_settings=war_value_settings,
    )

    drafted_picks = _extract_drafted_picks(
        raw_picks if isinstance(raw_picks, list) else [],
    )
    drafted_player_ids = {
        pick.player_id
        for pick in drafted_picks
    }
    available_player_values = [
        player
        for player in player_values
        if player.player_id not in drafted_player_ids
    ]

    available_assets_with_values = [
        (
            player,
            get_player_value(
                player=player,
                basis=value_basis,
                war_value_settings=war_value_settings,
            ),
        )
        for player in available_player_values
    ]

    auction_budget = _extract_auction_budget(
        raw_draft=raw_draft,
    )
    total_budget = auction_budget * max(
        league.total_rosters,
        1,
    )
    spent_budget = sum(
        pick.amount_paid
        for pick in drafted_picks
    )
    remaining_league_budget = max(
        total_budget - spent_budget,
        0,
    )

    fair_market_prices = _build_fair_market_prices(
        available_assets=available_assets_with_values,
        remaining_league_budget=remaining_league_budget,
    )

    details_service = LeagueDetails()
    seasonal_results = await details_service.build_roster_construction_seasonal_results(
        db=db,
        league=league,
        players=shared.players,
        current_shared=shared,
    )
    roster_targets = await build_cached_league_roster_construction_targets(
        redis=redis,
        league=league,
        roster_rows=rosters,
        seasonal_results=seasonal_results,
    )
    targets_by_position = {
        target.position: target.target_count
        for target in roster_targets
    }

    drafted_assets_by_roster_id: dict[
        int,
        list[AuctionDraftPlayerAsset]
    ] = {
        roster.roster_id: []
        for roster in rosters
    }

    for drafted_pick in drafted_picks:
        player_value = player_value_by_id.get(
            drafted_pick.player_id,
        )

        if player_value is None:
            continue

        selected_value = get_player_value(
            player=player_value,
            basis=value_basis,
            war_value_settings=war_value_settings,
        )

        drafted_assets_by_roster_id.setdefault(
            drafted_pick.roster_id,
            [],
        ).append(
            AuctionDraftPlayerAsset(
                player_id=player_value.player_id,
                name=player_value.name,
                position=player_value.position,
                team=player_value.team,
                age=player_value.age,
                underdog_position_rank=(
                    player_value.underdog_position_rank
                ),
                selected_value=selected_value,
                amount_paid=drafted_pick.amount_paid,
                budget_pct=round(
                    (
                        drafted_pick.amount_paid
                        / max(auction_budget, 1)
                    ) * 100,
                    1,
                ),
                value_per_dollar=round(
                    (selected_value or 0.0)
                    / drafted_pick.amount_paid,
                    3,
                ) if drafted_pick.amount_paid > 0 else None,
            )
        )

    league_target_rows = [
        AuctionDraftPositionSummary(
            position=target.position,
            target_count=target.target_count,
            drafted_count=0,
            spent_amount=0,
            spent_budget_pct=0.0,
            selected_value_total=round(
                target.war_share,
                1,
            ),
        )
        for target in roster_targets
    ]

    team_summaries: list[AuctionDraftTeamSummary] = []

    for roster in rosters:
        owner_name, owner_avatar = (
            _get_owner_name_and_avatar(
                roster_id=roster.roster_id,
                roster_by_id=roster_by_id,
                users_by_id=users_by_id,
            )
        )
        drafted_assets = sorted(
            drafted_assets_by_roster_id.get(
                roster.roster_id,
                [],
            ),
            key=lambda asset: (
                -asset.amount_paid,
                asset.name.lower(),
            ),
        )
        spent_amount = sum(
            asset.amount_paid
            for asset in drafted_assets
        )
        remaining_budget = max(
            auction_budget - spent_amount,
            0,
        )
        roster_capacity = roster.claimable_roster_capacity(
            league,
        )
        players_drafted = len(drafted_assets)
        roster_spots_left = max(
            roster_capacity - players_drafted,
            0,
        )
        acquired_value = round(
            sum(
                float(asset.selected_value or 0.0)
                for asset in drafted_assets
            ),
            3,
        )

        team_summaries.append(
            AuctionDraftTeamSummary(
                roster_id=roster.roster_id,
                owner_name=owner_name,
                owner_avatar=owner_avatar,
                players_drafted=players_drafted,
                roster_spots_left=roster_spots_left,
                spent_amount=spent_amount,
                spent_budget_pct=round(
                    (
                        spent_amount
                        / max(auction_budget, 1)
                    ) * 100,
                    1,
                ),
                remaining_budget=remaining_budget,
                max_bid=max(
                    remaining_budget
                    - max(
                        roster_spots_left - 1,
                        0,
                    ),
                    1,
                ) if roster_spots_left > 0 else remaining_budget,
                acquired_value=acquired_value,
                value_per_dollar=round(
                    acquired_value / spent_amount,
                    3,
                ) if spent_amount > 0 else None,
            )
        )

    team_summaries.sort(
        key=lambda summary: (
            -summary.acquired_value,
            summary.roster_id,
        ),
    )

    my_team_summary = next(
        (
            summary
            for summary in team_summaries
            if summary.roster_id == my_roster_id
        ),
        None,
    )

    if my_team_summary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not resolve your draft roster.",
        )

    my_drafted_assets = drafted_assets_by_roster_id.get(
        my_roster_id,
        [],
    )
    my_position_rows = _build_position_summary_rows(
        targets_by_position=targets_by_position,
        drafted_assets=my_drafted_assets,
        budget=auction_budget,
    )
    position_need_multipliers = _build_position_need_multipliers(
        roster_targets=my_position_rows,
    )
    weighted_available_total = sum(
        max(selected_value or 0.0, 0.0)
        * position_need_multipliers.get(
            player_value.position or "",
            1.0,
        )
        for player_value, selected_value in available_assets_with_values
    )

    filtered_available_assets = []
    normalized_search = (search or "").strip().lower()

    for player_value, selected_value in available_assets_with_values:
        if normalized_search and normalized_search not in (
            player_value.name.lower()
        ):
            continue

        filtered_available_assets.append(
            (
                player_value,
                selected_value,
            )
        )
    total_filtered_available = len(
        filtered_available_assets
    )

    filtered_available_assets.sort(
        key=lambda item: (
            -(item[1] or float("-inf")),
            item[0].name.lower(),
        ),
    )

    start = (page - 1) * page_size
    end = start + page_size
    paged_available_assets = filtered_available_assets[
        start:end
    ]

    available_players = []

    for player_value, selected_value in paged_available_assets:
        need_multiplier = position_need_multipliers.get(
            player_value.position or "",
            1.0,
        )
        weighted_share = (
            (
                max(selected_value or 0.0, 0.0)
                * need_multiplier
            ) / weighted_available_total
            if weighted_available_total > 0
            else 0.0
        )

        suggested_max_bid = min(
            my_team_summary.max_bid,
            max(
                round(
                    weighted_share
                    * max(
                        my_team_summary.remaining_budget,
                        1,
                    )
                ),
                1,
            ),
        )

        available_players.append(
            AuctionAvailablePlayerAsset(
                player_id=player_value.player_id,
                name=player_value.name,
                position=player_value.position,
                team=player_value.team,
                age=player_value.age,
                underdog_position_rank=(
                    player_value.underdog_position_rank
                ),
                selected_value=selected_value,
                fair_market_price=fair_market_prices.get(
                    player_value.player_id,
                    1,
                ),
                suggested_max_bid=suggested_max_bid,
                need_multiplier=need_multiplier,
            )
        )

    return AuctionDraftResponse(
        draft_id=draft_id,
        league_id=league.league_id,
        league_name=league.name,
        league_avatar=league.avatar,
        season=league.season,
        draft_status=raw_draft.get("status"),
        draft_type=raw_draft.get("type"),
        auction_budget=auction_budget,
        total_budget=total_budget,
        spent_budget=spent_budget,
        remaining_budget=remaining_league_budget,
        value_basis=value_basis.value,
        value_label=value_label,
        search=search,
        page=page,
        page_size=page_size,
        total_available_players=total_filtered_available,
        my_team=AuctionDraftMyTeam(
            roster_id=my_team_summary.roster_id,
            owner_name=my_team_summary.owner_name,
            owner_avatar=my_team_summary.owner_avatar,
            spent_amount=my_team_summary.spent_amount,
            spent_budget_pct=my_team_summary.spent_budget_pct,
            remaining_budget=my_team_summary.remaining_budget,
            max_bid=my_team_summary.max_bid,
            roster_size_target=roster_by_id[
                my_roster_id
            ].claimable_roster_capacity(
                league,
            ),
            players_drafted=my_team_summary.players_drafted,
            roster_spots_left=my_team_summary.roster_spots_left,
            acquired_value=my_team_summary.acquired_value,
            drafted_players=sorted(
                my_drafted_assets,
                key=lambda asset: (
                    -asset.amount_paid,
                    asset.name.lower(),
                ),
            ),
            position_summaries=my_position_rows,
        ),
        league_targets=league_target_rows,
        team_summaries=team_summaries,
        available_players=available_players,
    )
