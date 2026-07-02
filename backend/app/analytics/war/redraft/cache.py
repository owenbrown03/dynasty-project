from typing import Any


_WAR_CACHE: dict[str, list[Any]] = {}


def get_war_cache(
    league_id: str,
    season: int,
):
    key = f"{league_id}:{season}"

    return _WAR_CACHE.get(
        key
    )


def set_war_cache(
    league_id: str,
    season: int,
    value,
):
    key = f"{league_id}:{season}"

    _WAR_CACHE[key] = value


def clear_war_cache():
    _WAR_CACHE.clear()


def clear_league_war_cache(
    league_id: str,
    season: int,
):
    key = f"{league_id}:{season}"

    _WAR_CACHE.pop(
        key,
        None,
    )