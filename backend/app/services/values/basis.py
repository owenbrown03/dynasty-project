from __future__ import annotations

from enum import StrEnum

from app.schemas.player import PlayerValue
from app.services.values.war_settings import (
    WarValueConfig,
    WarValueSettings,
    normalize_war_value_settings,
)


class ValueBasis(StrEnum):
    KTC = "ktc"
    FANTASYCALC = "fantasycalc"
    ROOKIE_PICK_WAR = "rookie_pick_war"
    ADP = "adp"
    SLEEPER_WAR = "sleeper_war"
    MY_WAR = "my_war"

    REDRAFT_STARTER_WAR = "redraft_starter_war"
    REDRAFT_ROSTER_WAR = "redraft_roster_war"

    DYNASTY_STARTER_WAR = "dynasty_starter_war"
    DYNASTY_ROSTER_WAR = "dynasty_roster_war"


DEFAULT_VALUE_BASIS = ValueBasis.KTC


def _get_war_field(
    *,
    prefix: str,
    config: WarValueConfig,
) -> str:
    base = f"{config['timeframe']}_{config['scope']}_war"

    if not prefix:
        return base

    return f"{prefix}_{base}"


def _get_configured_war_value(
    *,
    player: PlayerValue,
    prefix: str,
    config: WarValueConfig,
) -> float | None:
    value = getattr(
        player,
        _get_war_field(
            prefix=prefix,
            config=config,
        ),
        None,
    )

    return (
        float(value)
        if value is not None
        else None
    )


def get_player_value(
    player: PlayerValue,
    basis: ValueBasis,
    war_value_settings: WarValueSettings | None = None,
) -> float | None:
    """
    Returns the player value for the selected valuation basis.

    Missing values remain None so a missing KTC/FantasyCalc/WAR value
    is never silently treated as zero.
    """

    normalized_war_settings = normalize_war_value_settings(
        war_value_settings,
    )

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

        case ValueBasis.ADP:
            return (
                float(player.adp_value)
                if player.adp_value is not None
                else None
            )

        case ValueBasis.ROOKIE_PICK_WAR:
            return None

        case ValueBasis.SLEEPER_WAR:
            return _get_configured_war_value(
                player=player,
                prefix="",
                config=normalized_war_settings[
                    "sleeper_projection"
                ],
            )

        case ValueBasis.MY_WAR:
            return _get_configured_war_value(
                player=player,
                prefix="my",
                config=normalized_war_settings["my"],
            )

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
    war_value_settings: WarValueSettings | None = None,
) -> str:
    normalized_war_settings = normalize_war_value_settings(
        war_value_settings,
    )

    match basis:
        case ValueBasis.KTC:
            return "KTC Value"

        case ValueBasis.FANTASYCALC:
            return "FantasyCalc Value"

        case ValueBasis.ADP:
            return "ADP Value"

        case ValueBasis.ROOKIE_PICK_WAR:
            return "Rookie Pick WAR"

        case ValueBasis.SLEEPER_WAR:
            config = normalized_war_settings[
                "sleeper_projection"
            ]
            return (
                f"Sleeper {config['timeframe'].title()} "
                f"{config['scope'].title()} WAR"
            )

        case ValueBasis.MY_WAR:
            config = normalized_war_settings["my"]
            return (
                f"My {config['timeframe'].title()} "
                f"{config['scope'].title()} WAR"
            )

        case ValueBasis.REDRAFT_STARTER_WAR:
            return "Redraft Starter WAR"

        case ValueBasis.REDRAFT_ROSTER_WAR:
            return "Redraft Roster WAR"

        case ValueBasis.DYNASTY_STARTER_WAR:
            return "Dynasty Starter WAR"

        case ValueBasis.DYNASTY_ROSTER_WAR:
            return "Dynasty Roster WAR"

    return "Value"
