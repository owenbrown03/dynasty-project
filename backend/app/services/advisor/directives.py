from __future__ import annotations

import logging

from app.schemas.advisor import (
    AdvisorDirective,
    AdvisorDirectivesResponse,
    AdvisorPlayerRef,
)
from app.schemas.personal_values import PersonalValuePoolItem
from app.services.leagues.selection import (
    get_visible_owned_league_rows_by_sleeper_user_id,
)
from app.services.personal_values import get_personal_value_pool

logger = logging.getLogger(__name__)

def _drop_value(item: PersonalValuePoolItem) -> float:
    """Drop-candidate ranking: the manager's OWN value system.

    Lowest personal WAR gets cut first. Players missing personal
    values sort as pure cut candidates rather than crashing.
    """
    metrics = item.custom_values

    war = getattr(metrics, "dynasty_roster_war", None)
    if war is None:
        war = getattr(metrics, "redraft_roster_war", None)

    return float(war) if war is not None else 0.0


def _to_ref(item: PersonalValuePoolItem) -> AdvisorPlayerRef:
    return AdvisorPlayerRef(
        player_id=item.player.player_id,
        name=item.player.name,
        position=item.player.position,
        team=item.player.team,
        age=item.player.age,
        market_value=(
            float(item.player.fc_value)
            if item.player.fc_value is not None
            else None
        ),
    )


async def build_advisor_directives(
    ctx,
    username: str,
    *,
    league_id: str | None = None,
) -> AdvisorDirectivesResponse:
    """Deterministic roster directives across the user's leagues.

    Currently emits one directive per over-capacity league with the
    lowest-value cut candidates. Capacity math stays centralized in
    Roster.claimable_roster_capacity / open_roster_spots so waiver
    claims and these directives always agree.
    """
    connection = ctx.connection

    if connection is None or ctx.db is None:
        return AdvisorDirectivesResponse(directives=[])

    rows = await get_visible_owned_league_rows_by_sleeper_user_id(
        db=ctx.db,
        sleeper_user_id=connection.sleeper_user_id,
        site_user_id=(
            ctx.site_user.id if ctx.site_user else None
        ),
    )

    if league_id is not None:
        rows = [
            row
            for row in rows
            if row.league.league_id == league_id
        ]

    directives: list[AdvisorDirective] = []

    for row in rows:
        league = row.league
        roster = row.roster

        over_by = -roster.open_roster_spots(league)
        if over_by <= 0:
            continue

        try:
            pool = await get_personal_value_pool(
                ctx=ctx,
                league_id=league.league_id,
            )
        except Exception:
            logger.exception(
                "Advisor directive value pool fetch failed "
                "league=%s",
                league.league_id,
            )
            continue

        items_by_player_id = {
            item.player.player_id: item
            for group in pool.groups
            for item in group.players
        }

        # In standard leagues occupied IR/taxi slots add capacity, so
        # cutting those stash players is unnecessary; in best ball
        # they consume general spots and are legitimate cuts.
        parked_ids = set()
        if not league.is_best_ball:
            parked_ids = {
                *(roster.reserve or []),
                *(roster.taxi or []),
            }

        candidates = [
            items_by_player_id[pid]
            for pid in (roster.players or [])
            if pid in items_by_player_id and pid not in parked_ids
        ]

        drops = sorted(
            candidates,
            key=lambda item: (
                _drop_value(item),
                item.player.name,
            ),
        )[:over_by]

        directives.append(
            AdvisorDirective(
                league_id=league.league_id,
                league_name=league.name,
                season=league.season,
                status=league.status,
                total_rosters=league.total_rosters,
                over_limit_by=over_by,
                suggested_drops=[_to_ref(item) for item in drops],
            )
        )

    return AdvisorDirectivesResponse(directives=directives)
