from __future__ import annotations

from collections.abc import Iterable

from app.analytics.war.dynasty.models import (
    DynastyPlayerInput,
    DynastyProjection,
)
from app.analytics.war.dynasty.service import DynastyWARService
from app.analytics.war.redraft.models import PlayerWAR
from .constants import WAIVER_CANDIDATE_LIMIT

DYNASTY_FANTASY_POSITIONS = {
    "QB",
    "RB",
    "WR",
    "TE",
}


def build_dynasty_projection(
    player_war: PlayerWAR,
    dynasty_service: DynastyWARService,
) -> DynastyProjection | None:
    """
    Converts a league-specific redraft WAR record into dynasty WAR.

    Dynasty value is currently only supported for QB/RB/WR/TE because
    ExpectedGamesRemainingService only has aging/retirement tables for
    those positions.
    """

    if player_war.position not in DYNASTY_FANTASY_POSITIONS:
        return None

    if player_war.age is None:
        return None

    return dynasty_service.project_player(
        DynastyPlayerInput(
            player_id=player_war.player_id,
            name=player_war.name,
            position=player_war.position,
            team=player_war.team,
            age=player_war.age,
            starter_war=player_war.starter_war or 0.0,
            roster_war=player_war.roster_war or 0.0,
        )
    )


def project_players_for_waivers(
    *,
    player_war_results: Iterable[PlayerWAR],
    available_player_ids: set[str],
    user_roster_player_ids: set[str],
    dynasty_service: DynastyWARService,
) -> dict[str, DynastyProjection]:
    """
    Produces dynasty values for waiver-relevant QB/RB/WR/TE players only.

    We project:
    - top available players by current redraft roster WAR
    - all QB/RB/WR/TE players on the user's roster

    Placeholder positions such as LB, DB, DL, IDP, DEF, K, or custom
    league-only positions are ignored by the dynasty model.
    """

    player_war_by_id = {
        player.player_id: player
        for player in player_war_results
        if player.position in DYNASTY_FANTASY_POSITIONS
    }

    available_candidates = sorted(
        (
            player_war_by_id[player_id]
            for player_id in available_player_ids
            if player_id in player_war_by_id
        ),
        key=lambda player: player.roster_war or 0.0,
        reverse=True,
    )[:WAIVER_CANDIDATE_LIMIT]

    roster_candidates = [
        player_war_by_id[player_id]
        for player_id in user_roster_player_ids
        if player_id in player_war_by_id
    ]

    dynasty_by_player_id: dict[str, DynastyProjection] = {}

    for player_war in available_candidates + roster_candidates:
        if player_war.player_id in dynasty_by_player_id:
            continue

        dynasty_projection = build_dynasty_projection(
            player_war=player_war,
            dynasty_service=dynasty_service,
        )

        if dynasty_projection is not None:
            dynasty_by_player_id[
                player_war.player_id
            ] = dynasty_projection

    return dynasty_by_player_id