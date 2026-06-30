import logging
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.sleeper.api import Player
from app.models.db.underdog.models import UnderdogPlayerMap, UnderdogADP
from app.integrations.underdog import UnderdogClient
from app.integrations.sleeper.client import SleeperClient
from app.services.sleeper.normalize import SleeperNameIndex

logger = logging.getLogger(__name__)


async def sync_underdog_adp(
    db: AsyncSession,
    underdog: UnderdogClient,
    *,
    superflex: bool = False,
) -> dict:
    """
    Pulls current Underdog NFL best ball ADP, matches each player to our
    canonical Sleeper player_id, and upserts UnderdogPlayerMap + UnderdogADP.
    """

    logger.info(f"Starting Underdog ADP sync (superflex={superflex})")

    # --------------------------------------------------
    # 1. Build the Sleeper name index from our own DB
    #    (avoids re-hitting the Sleeper API every sync)
    # --------------------------------------------------
    result = await db.execute(select(Player))
    db_players = result.scalars().all()

    sleeper_lookup = {
        p.player_id: type(
            "P", (), {"first_name": p.first_name, "last_name": p.last_name, "team": p.team}
        )()
        for p in db_players
    }
    name_index = SleeperNameIndex(sleeper_lookup)

    # --------------------------------------------------
    # 2. Pull enriched appearances from Underdog
    # --------------------------------------------------
    appearances = await underdog.read.get_nfl_adp(superflex=superflex)

    # Filter out zero-ADP noise (inactive/practice squad players)
    appearances = [
        a for a in appearances
        if a.projection and _safe_float(a.projection.adp) > 0
    ]

    logger.info(f"Fetched {len(appearances)} Underdog appearances with ADP > 0")

    # --------------------------------------------------
    # 3. Load existing maps so we don't re-fuzzy-match every run
    # --------------------------------------------------
    result = await db.execute(select(UnderdogPlayerMap))
    existing_maps = {m.underdog_id: m for m in result.scalars().all()}

    matched = 0
    unmatched: list[str] = []
    new_maps = []
    new_adp_rows = []

    for app in appearances:
        if not app.player:
            continue

        underdog_id = app.player_id
        existing = existing_maps.get(underdog_id)

        if existing:
            player_id = existing.player_id
        else:
            full_name = f"{app.player.first_name} {app.player.last_name}"
            team = app.team_abbr or ""

            player_id, matched_via, confidence = name_index.match(full_name, team=team)

            if not player_id:
                unmatched.append(f"{full_name} ({team}) ADP {app.projection.adp}")
                continue

            new_maps.append(
                UnderdogPlayerMap(
                    underdog_id=underdog_id,
                    player_id=player_id,
                    matched_via=matched_via,
                    confidence=confidence,
                )
            )

        matched += 1

        proj = app.projection
        new_adp_rows.append(
            UnderdogADP(
                player_id=player_id,
                slate_id=app.match_id and str(app.match_id) or "",
                scoring_type_id=proj.scoring_type_id,
                superflex=superflex,
                adp=_safe_float(proj.adp),
                position_rank=proj.position_rank,
                avg_weekly_points=_safe_float(proj.avg_weekly_points, default=None),
                salary=_safe_float(proj.salary, default=None),
            )
        )

    logger.info(f"Matched: {matched}/{len(appearances)}")
    if unmatched:
        logger.info(f"Unmatched ({len(unmatched)}):\n" + "\n".join(f"  {u}" for u in unmatched))

    # --------------------------------------------------
    # 4. Persist
    # --------------------------------------------------
    for m in new_maps:
        db.add(m)

    for row in new_adp_rows:
        existing_adp = await db.execute(
            select(UnderdogADP).where(
                UnderdogADP.player_id == row.player_id,
                UnderdogADP.slate_id == row.slate_id,
                UnderdogADP.scoring_type_id == row.scoring_type_id,
            )
        )
        existing_row = existing_adp.scalar_one_or_none()
        if existing_row:
            existing_row.adp = row.adp
            existing_row.position_rank = row.position_rank
            existing_row.avg_weekly_points = row.avg_weekly_points
            existing_row.salary = row.salary
            db.add(existing_row)
        else:
            db.add(row)

    await db.commit()

    return {
        "fetched": len(appearances),
        "matched": matched,
        "unmatched": len(unmatched),
        "unmatched_names": unmatched,
        "new_maps_created": len(new_maps),
    }


def _safe_float(value, default: float | None = 0.0):
    if value is None or value == "-":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default