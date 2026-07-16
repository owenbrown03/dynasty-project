from __future__ import annotations

import json

from app.analytics.war.redraft.models import PlayerWAR
from app.analytics.war.redraft.service import WARService
from app.models.db.sleeper.api import League


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


async def build_shared_redraft_war_by_league_id(
    *,
    db,
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
                await war_service.calculate_with_data(
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
