from __future__ import annotations

import hashlib
import json

from app.analytics.war.dynasty.factory import build_dynasty_war_service
from app.analytics.war.dynasty.models import DynastyProjection
from app.analytics.war.redraft.models import PlayerWAR
from app.analytics.war.redraft.service import WARService
from app.infrastructure.redis.client import RedisClient
from app.models.db.sleeper.api import League
from app.services.waivers.dynasty import build_dynasty_projection

DYNASTY_PROJECTION_CACHE_TTL_SECONDS = (
    6 * 60 * 60
)
DYNASTY_PROJECTION_CACHE_VERSION = "v1"


def build_league_war_fingerprint(
    *,
    league: League,
) -> str:
    return json.dumps(
        {
            "season": league.season,
            "total_rosters": league.total_rosters,
            "scoring_settings": (
                league.scoring_settings
            ),
            "roster_positions": (
                league.roster_positions
            ),
        },
        sort_keys=True,
    )


def build_player_war_signature(
    *,
    player_wars: list[PlayerWAR],
) -> str:
    digest = hashlib.sha256()
    digest.update(
        json.dumps(
            [
                {
                    "player_id": player.player_id,
                    "name": player.name,
                    "position": player.position,
                    "team": player.team,
                    "age": player.age,
                    "starter_war": player.starter_war,
                    "roster_war": player.roster_war,
                    "model_version": player.model_version,
                }
                for player in sorted(
                    player_wars,
                    key=lambda player: player.player_id,
                )
            ],
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    return digest.hexdigest()


async def build_cached_dynasty_projections_by_player_id(
    *,
    redis: RedisClient | None,
    player_wars: list[PlayerWAR],
) -> dict[str, DynastyProjection]:
    if not player_wars:
        return {}

    cache_key = (
        "dynasty-projection:"
        f"{DYNASTY_PROJECTION_CACHE_VERSION}:"
        f"{build_player_war_signature(player_wars=player_wars)}"
    )

    if redis is not None:
        cached_payload = await redis.get(
            cache_key,
        )

        if cached_payload:
            return {
                player_id: DynastyProjection.model_validate(
                    payload,
                )
                for player_id, payload in json.loads(
                    cached_payload,
                ).items()
            }

    dynasty_service = build_dynasty_war_service()
    dynasty_by_player_id: dict[str, DynastyProjection] = {}

    for player_war in player_wars:
        if player_war.player_id in dynasty_by_player_id:
            continue

        projection = build_dynasty_projection(
            player_war=player_war,
            dynasty_service=dynasty_service,
        )

        if projection is not None:
            dynasty_by_player_id[
                player_war.player_id
            ] = projection

    if redis is not None:
        await redis.set(
            cache_key,
            json.dumps(
                {
                    player_id: projection.model_dump()
                    for player_id, projection in (
                        dynasty_by_player_id.items()
                    )
                },
                separators=(",", ":"),
            ),
            ttl_seconds=(
                DYNASTY_PROJECTION_CACHE_TTL_SECONDS
            ),
        )

    return dynasty_by_player_id


async def build_shared_redraft_war_by_league_id(
    *,
    db,
    redis: RedisClient | None,
    leagues: list[League],
    war_service: WARService,
) -> dict[str, list[PlayerWAR]]:
    war_by_fingerprint: dict[
        str,
        list[PlayerWAR],
    ] = {}
    shared_by_season: dict[int, object] = {}
    war_by_league_id: dict[
        str,
        list[PlayerWAR],
    ] = {}

    for league in leagues:
        fingerprint = build_league_war_fingerprint(
            league=league,
        )

        if fingerprint not in war_by_fingerprint:
            projection_season = int(league.season)

            if projection_season not in shared_by_season:
                shared_by_season[
                    projection_season
                ] = await war_service.load_shared_data(
                    db,
                    projection_season,
                )

            war_by_fingerprint[fingerprint] = (
                await war_service.calculate_with_shared_cache(
                    redis=redis,
                    league=league,
                    shared=shared_by_season[
                        projection_season
                    ],
                )
            )

        war_by_league_id[
            league.league_id
        ] = war_by_fingerprint[fingerprint]

    return war_by_league_id
