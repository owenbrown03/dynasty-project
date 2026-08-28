from __future__ import annotations

from dataclasses import dataclass
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
    SLEEPER_PROJECTION = "sleeper_projection"
    MY_ROSTER_WAR = "my_roster_war"
    MY_STARTER_WAR = "my_starter_war"

    REDRAFT_STARTER_WAR = "redraft_starter_war"
    REDRAFT_ROSTER_WAR = "redraft_roster_war"

    DYNASTY_STARTER_WAR = "dynasty_starter_war"
    DYNASTY_ROSTER_WAR = "dynasty_roster_war"

    KTC_REDRAFT = "ktc_redraft"
    FANTASYCALC_REDRAFT = "fantasycalc_redraft"


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


@dataclass(frozen=True)
class ValueBasisSpec:
    """What a value basis needs to produce numbers.

    Single source of truth for feature gates (tier board, exports,
    future consumers). A basis missing from this registry is a bug:
    the completeness test in the suite will fail.
    """

    needs_league_context: bool = False
    needs_personal_hydration: bool = False
    needs_dynasty_projections: bool = False


VALUE_BASIS_SPECS: dict[ValueBasis, ValueBasisSpec] = {
    ValueBasis.KTC: ValueBasisSpec(),
    ValueBasis.FANTASYCALC: ValueBasisSpec(),
    ValueBasis.ADP: ValueBasisSpec(),
    ValueBasis.ROOKIE_PICK_WAR: ValueBasisSpec(),
    ValueBasis.SLEEPER_PROJECTION: ValueBasisSpec(
        needs_league_context=True,
    ),
    ValueBasis.SLEEPER_WAR: ValueBasisSpec(
        needs_league_context=True,
        needs_dynasty_projections=True,
    ),
    ValueBasis.MY_WAR: ValueBasisSpec(
        needs_league_context=True,
        needs_personal_hydration=True,
        needs_dynasty_projections=True,
    ),
    ValueBasis.MY_ROSTER_WAR: ValueBasisSpec(
        needs_league_context=True,
        needs_personal_hydration=True,
        needs_dynasty_projections=True,
    ),
    ValueBasis.MY_STARTER_WAR: ValueBasisSpec(
        needs_league_context=True,
        needs_personal_hydration=True,
        needs_dynasty_projections=True,
    ),
    ValueBasis.REDRAFT_STARTER_WAR: ValueBasisSpec(
        needs_league_context=True,
    ),
    ValueBasis.REDRAFT_ROSTER_WAR: ValueBasisSpec(
        needs_league_context=True,
    ),
    ValueBasis.DYNASTY_STARTER_WAR: ValueBasisSpec(
        needs_league_context=True,
        needs_dynasty_projections=True,
    ),
    ValueBasis.DYNASTY_ROSTER_WAR: ValueBasisSpec(
        needs_league_context=True,
        needs_dynasty_projections=True,
    ),
    ValueBasis.KTC_REDRAFT: ValueBasisSpec(),
    ValueBasis.FANTASYCALC_REDRAFT: ValueBasisSpec(),
}


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

        case ValueBasis.SLEEPER_PROJECTION:
            return player.projected_points

        case ValueBasis.MY_ROSTER_WAR:
            return player.my_dynasty_roster_war

        case ValueBasis.MY_STARTER_WAR:
            return player.my_dynasty_starter_war

        case ValueBasis.REDRAFT_STARTER_WAR:
            return player.redraft_starter_war

        case ValueBasis.REDRAFT_ROSTER_WAR:
            return player.redraft_roster_war

        case ValueBasis.DYNASTY_STARTER_WAR:
            return player.dynasty_starter_war

        case ValueBasis.DYNASTY_ROSTER_WAR:
            return player.dynasty_roster_war

        case ValueBasis.KTC_REDRAFT:
            return player.ktc_redraft_value

        case ValueBasis.FANTASYCALC_REDRAFT:
            return player.fc_redraft_value

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

        case ValueBasis.KTC_REDRAFT:
            return "KTC (redraft)"

        case ValueBasis.FANTASYCALC_REDRAFT:
            return "FantasyCalc (redraft)"

    return "Value"
