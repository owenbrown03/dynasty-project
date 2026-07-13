from __future__ import annotations

from enum import StrEnum

from app.schemas.player import PlayerValue


class ValueBasis(StrEnum):
    KTC = "ktc"
    FANTASYCALC = "fantasycalc"
    MY_WAR = "my_war"

    REDRAFT_STARTER_WAR = "redraft_starter_war"
    REDRAFT_ROSTER_WAR = "redraft_roster_war"

    DYNASTY_STARTER_WAR = "dynasty_starter_war"
    DYNASTY_ROSTER_WAR = "dynasty_roster_war"


DEFAULT_VALUE_BASIS = ValueBasis.KTC


def get_player_value(
    player: PlayerValue,
    basis: ValueBasis,
) -> float | None:
    """
    Returns the player value for the selected valuation basis.

    Missing values remain None so a missing KTC/FantasyCalc/WAR value
    is never silently treated as zero.
    """

    match basis:
        case ValueBasis.KTC:
            return (
                float(player.ktc_value)
                if player.ktc_value is not None
                else None
            )

        case ValueBasis.FANTASYCALC:
            return (
                float(player.fc_value)
                if player.fc_value is not None
                else None
            )

        case ValueBasis.MY_WAR:
            return player.my_dynasty_roster_war

        case ValueBasis.REDRAFT_STARTER_WAR:
            return player.redraft_starter_war

        case ValueBasis.REDRAFT_ROSTER_WAR:
            return player.redraft_roster_war

        case ValueBasis.DYNASTY_STARTER_WAR:
            return player.dynasty_starter_war

        case ValueBasis.DYNASTY_ROSTER_WAR:
            return player.dynasty_roster_war

    return None


def get_value_label(
    basis: ValueBasis,
) -> str:
    match basis:
        case ValueBasis.KTC:
            return "KTC Value"

        case ValueBasis.FANTASYCALC:
            return "FantasyCalc Value"

        case ValueBasis.MY_WAR:
            return "My WAR"

        case ValueBasis.REDRAFT_STARTER_WAR:
            return "Redraft Starter WAR"

        case ValueBasis.REDRAFT_ROSTER_WAR:
            return "Redraft Roster WAR"

        case ValueBasis.DYNASTY_STARTER_WAR:
            return "Dynasty Starter WAR"

        case ValueBasis.DYNASTY_ROSTER_WAR:
            return "Dynasty Roster WAR"

    return "Value"
