from __future__ import annotations

from math import floor

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.war.redraft.singleton import war_service
from app.core.context import Context
from app.crud.sleeper.player import (
    get_latest_projection_season,
    get_supported_player_ids,
)
from app.crud.sleeper.roster import get_owned_roster_rows
from app.crud.value import get_player_values
from app.schemas.player import PlayerValue
from app.schemas.player_tiers import (
    PlayerTierBoardResponse,
    TierGroup,
    TierPlayer,
)
from app.services.values.basis import (
    ValueBasis,
    get_player_value,
    get_value_label,
)
from app.services.values.war_settings import WarValueSettings
from app.services.values.canonical import (
    build_canonical_war_league,
)
from app.services.personal_values import hydrate_personal_player_values
from app.services.war.shared import (
    build_cached_dynasty_projections_by_player_id,
)


TIER_LABELS = [
    "S+",
    "S",
    "S-",
    "A+",
    "A",
    "A-",
    "B+",
    "B",
    "B-",
    "C+",
    "C",
    "C-",
    "D+",
    "D",
    "D-",
    "F+",
    "F",
    "F-",
]

MAX_TIER_PLAYERS = 500

def assign_tier_label(
    *,
    selected_value: float,
    min_value: float,
    max_value: float,
) -> str:
    if max_value <= min_value:
        return TIER_LABELS[
            floor(
                len(TIER_LABELS) / 2,
            )
        ]

    normalized = (
        selected_value - min_value
    ) / (
        max_value - min_value
    )

    bucket_index = min(
        len(TIER_LABELS) - 1,
        floor(
            normalized * len(TIER_LABELS),
        ),
    )

    label_index = (
        len(TIER_LABELS) - 1 - bucket_index
    )

    return TIER_LABELS[label_index]


async def build_dynasty_values_by_player_id(
    *,
    redis,
    players: list,
) -> dict[str, object]:
    return await build_cached_dynasty_projections_by_player_id(
        redis=redis,
        player_wars=list(players),
    )


async def load_player_values_for_basis(
    *,
    db: AsyncSession,
    redis,
    value_basis: ValueBasis,
    site_user_id=None,
    war_value_settings: WarValueSettings | None = None,
    league=None,
    season: int,
) -> list[PlayerValue]:
    supported_player_ids = await get_supported_player_ids(
        db,
    )

    if not supported_player_ids:
        return []

    if value_basis in {
        ValueBasis.KTC,
        ValueBasis.FANTASYCALC,
    }:
        return await get_player_values(
            db,
            player_ids=supported_player_ids,
            redraft_war_players=[],
            dynasty_war_by_player_id={},
        )

    shared = await war_service.load_shared_data(
        db,
        season,
    )

    war_players = await war_service.calculate_with_data(
        league=league,
        shared=shared,
    )

    dynasty_war_by_player_id = {}

    if value_basis in {
        ValueBasis.DYNASTY_STARTER_WAR,
        ValueBasis.DYNASTY_ROSTER_WAR,
        ValueBasis.SLEEPER_WAR,
        ValueBasis.MY_WAR,
    }:
        dynasty_war_by_player_id = (
            await build_dynasty_values_by_player_id(
                redis=redis,
                players=war_players,
            )
        )

    player_values = await get_player_values(
        db,
        player_ids=[player.player_id for player in war_players],
        redraft_war_players=war_players,
        dynasty_war_by_player_id=dynasty_war_by_player_id,
    )

    if value_basis == ValueBasis.MY_WAR and league is not None:
        player_values = await hydrate_personal_player_values(
            db=db,
            site_user_id=site_user_id,
            league=league,
            player_values=player_values,
            redis=redis,
        )

    return player_values


async def resolve_league_war_context(
    *,
    ctx: Context,
    league_id: str,
):
    if ctx.connection is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="League WAR requires a linked Sleeper account.",
        )

    owned_rows = await get_owned_roster_rows(
        db=ctx.db,
        connection=ctx.connection,
    )

    for _, league in owned_rows:
        if league.league_id == league_id:
            return league

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Selected league was not found in your linked leagues.",
    )


async def get_player_tier_board(
    *,
    ctx: Context,
    value_basis: ValueBasis,
    league_id: str | None = None,
) -> PlayerTierBoardResponse:
    season = await get_latest_projection_season(
        ctx.db,
    )

    if season is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Player projections are not available yet.",
        )

    war_league_name: str | None = None
    war_context = "global"
    league = None

    if value_basis in {
        ValueBasis.REDRAFT_STARTER_WAR,
        ValueBasis.REDRAFT_ROSTER_WAR,
        ValueBasis.DYNASTY_STARTER_WAR,
        ValueBasis.DYNASTY_ROSTER_WAR,
        ValueBasis.SLEEPER_WAR,
        ValueBasis.MY_WAR,
    }:
        if league_id:
            league = await resolve_league_war_context(
                ctx=ctx,
                league_id=league_id,
            )
            war_context = "league"
            war_league_name = league.name
        else:
            league = build_canonical_war_league(
                season,
            )

    effective_season = (
        int(league.season)
        if league is not None and hasattr(league, "season")
        else season
    )

    player_values = await load_player_values_for_basis(
        db=ctx.db,
        redis=ctx.redis,
        value_basis=value_basis,
        site_user_id=ctx.site_user.id if ctx.site_user else None,
        war_value_settings=ctx.site_user.settings.get("war_value_settings")
        if ctx.site_user and ctx.site_user.settings
        else None,
        league=league,
        season=effective_season,
    )
    war_value_settings = (
        ctx.site_user.settings.get("war_value_settings")
        if ctx.site_user and ctx.site_user.settings
        else None
    )

    ranked_players = []

    for player in player_values:
        selected_value = get_player_value(
            player,
            value_basis,
            war_value_settings,
        )

        if selected_value is None:
            continue

        ranked_players.append(
            (
                player,
                float(selected_value),
            )
        )

    ranked_players.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    ranked_players = ranked_players[:MAX_TIER_PLAYERS]

    if ranked_players:
        max_value = ranked_players[0][1]
        min_value = ranked_players[-1][1]
    else:
        max_value = 0.0
        min_value = 0.0

    tier_groups = {
        label: TierGroup(
            label=label,
            players=[],
        )
        for label in TIER_LABELS
    }

    for index, (player, selected_value) in enumerate(
        ranked_players,
        start=1,
    ):
        tier_label = assign_tier_label(
            selected_value=selected_value,
            min_value=min_value,
            max_value=max_value,
        )

        tier_groups[tier_label].players.append(
            TierPlayer(
                player_id=player.player_id,
                name=player.name,
                position=player.position,
                team=player.team,
                age=player.age,
                rank=index,
                tier=tier_label,
                selected_value=selected_value,
            )
        )

    return PlayerTierBoardResponse(
        value_basis=value_basis,
        value_label=get_value_label(
            value_basis,
            war_value_settings,
        ),
        season=effective_season,
        war_context=war_context,
        war_league_id=league_id if war_context == "league" else None,
        war_league_name=war_league_name,
        tiers=[
            tier_groups[label]
            for label in TIER_LABELS
        ],
    )
