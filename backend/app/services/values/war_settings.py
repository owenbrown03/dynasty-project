from __future__ import annotations

from typing import Literal, TypedDict


WarTimeframe = Literal["redraft", "dynasty"]
WarScope = Literal["starter", "roster"]


class WarValueConfig(TypedDict):
    timeframe: WarTimeframe
    scope: WarScope


class WarValueSettings(TypedDict):
    sleeper_projection: WarValueConfig
    my: WarValueConfig


DEFAULT_WAR_VALUE_CONFIG: WarValueConfig = {
    "timeframe": "dynasty",
    "scope": "roster",
}

DEFAULT_WAR_VALUE_SETTINGS: WarValueSettings = {
    "sleeper_projection": DEFAULT_WAR_VALUE_CONFIG,
    "my": DEFAULT_WAR_VALUE_CONFIG,
}

VALID_TIMEFRAMES = {"redraft", "dynasty"}
VALID_SCOPES = {"starter", "roster"}


def normalize_war_value_config(
    value,
) -> WarValueConfig:
    if not isinstance(value, dict):
        return dict(DEFAULT_WAR_VALUE_CONFIG)

    timeframe = value.get("timeframe")
    scope = value.get("scope")

    return {
        "timeframe": (
            timeframe
            if timeframe in VALID_TIMEFRAMES
            else DEFAULT_WAR_VALUE_CONFIG["timeframe"]
        ),
        "scope": (
            scope
            if scope in VALID_SCOPES
            else DEFAULT_WAR_VALUE_CONFIG["scope"]
        ),
    }


def normalize_war_value_settings(
    value,
) -> WarValueSettings:
    if not isinstance(value, dict):
        return {
            "sleeper_projection": dict(DEFAULT_WAR_VALUE_CONFIG),
            "my": dict(DEFAULT_WAR_VALUE_CONFIG),
        }

    return {
        "sleeper_projection": normalize_war_value_config(
            value.get("sleeper_projection"),
        ),
        "my": normalize_war_value_config(
            value.get("my"),
        ),
    }
