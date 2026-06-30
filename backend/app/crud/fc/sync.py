import logging

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.sleeper.api import Player
from app.models.db.fc.models import FantasyCalcValue
from app.integrations.fc.client import FantasyCalcClient


logger = logging.getLogger(__name__)


async def sync_fantasycalc_values(
    db: AsyncSession,
    fc: FantasyCalcClient,
    *,
    is_dynasty: bool = True,
    num_qbs: int = 2,
    num_teams: int = 12,
    ppr: int = 1,
) -> dict:

    logger.info(
        "Starting FantasyCalc sync"
    )


    # ------------------------------------
    # Fetch FantasyCalc
    # ------------------------------------

    players = await fc.read.get_current_values(
        is_dynasty=is_dynasty,
        num_qbs=num_qbs,
        num_teams=num_teams,
        ppr=ppr,
    )


    logger.info(
        f"Fetched {len(players)} FantasyCalc players"
    )


    # ------------------------------------
    # Existing Sleeper players
    # ------------------------------------

    result = await db.execute(
        select(Player)
    )

    sleeper_players = {
        p.player_id: p
        for p in result.scalars()
    }


    matched = 0
    unmatched = []

    rows = []


    # ------------------------------------
    # Convert FantasyCalc -> DB rows
    # ------------------------------------

    for fc in players:

        sleeper_id = fc.player.sleeperId

        if not sleeper_id:
            unmatched.append(
                fc.player.name
            )
            continue


        if sleeper_id not in sleeper_players:
            unmatched.append(
                f"{fc.player.name} ({sleeper_id})"
            )
            continue


        matched += 1

        rows.append(
            FantasyCalcValue(
                player_id=sleeper_id,

                is_dynasty=is_dynasty,
                num_qbs=num_qbs,
                num_teams=num_teams,
                ppr=ppr,

                value=fc.value,
                overall_rank=fc.overallRank,
                position_rank=fc.positionRank,

                trend_30_day=fc.trend30Day,

                redraft_value=fc.redraftValue,
                combined_value=fc.combinedValue,

                tier=fc.maybeTier,
                adp=fc.maybeAdp,
            )
        )


    # ------------------------------------
    # Upsert
    # ------------------------------------

    updated = 0
    created = 0


    for row in rows:

        result = await db.execute(
            select(FantasyCalcValue).where(
                FantasyCalcValue.player_id == row.player_id,
                FantasyCalcValue.is_dynasty == row.is_dynasty,
                FantasyCalcValue.num_qbs == row.num_qbs,
                FantasyCalcValue.num_teams == row.num_teams,
                FantasyCalcValue.ppr == row.ppr,
            )
        )

        existing = result.scalar_one_or_none()


        if existing:

            for field in (
                "value",
                "overall_rank",
                "position_rank",
                "trend_30_day",
                "redraft_value",
                "combined_value",
                "tier",
                "adp",
            ):
                setattr(
                    existing,
                    field,
                    getattr(row, field),
                )

            db.add(existing)
            updated += 1

        else:
            db.add(row)
            created += 1


    await db.commit()


    logger.info(
        f"FantasyCalc sync complete "
        f"matched={matched} created={created} updated={updated}"
    )


    return {
        "fetched": len(players),
        "matched": matched,
        "unmatched": len(unmatched),
        "created": created,
        "updated": updated,
        "unmatched_names": unmatched,
    }