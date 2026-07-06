from __future__ import annotations

from .models import (
    DynastyPlayerInput,
    DynastyProjection,
)
from .service import DynastyWARService
from ..redraft.models import PlayerWAR


def project_dynasty_war(
    war_players: list[PlayerWAR],
    dynasty_service: DynastyWARService,
) -> dict[str, DynastyProjection]:
    """
    Converts league-specific redraft WAR into dynasty WAR.

    A player must have an age and position because the dynasty model needs
    both to calculate expected games remaining and aging decline.
    """

    dynasty_by_player_id: dict[str, DynastyProjection] = {}

    for war_player in war_players:
        if war_player.age is None:
            continue

        if not war_player.position:
            continue

        projection = dynasty_service.project_player(
            DynastyPlayerInput(
                player_id=war_player.player_id,
                name=war_player.name,
                position=war_player.position,
                team=war_player.team,
                age=war_player.age,
                starter_war=war_player.starter_war or 0.0,
                roster_war=war_player.roster_war or 0.0,
            )
        )

        dynasty_by_player_id[war_player.player_id] = projection

    return dynasty_by_player_id