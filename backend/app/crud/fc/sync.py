import logging

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.sleeper.api import Player
from app.models.db.fc.models import FantasyCalcValue, FantasyCalcPickValue
from app.integrations.fc.client import FantasyCalcClient
from app.services.draft.values import parse_fantasycalc_pick


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
    pick_rows = []


    # ------------------------------------
    # Convert FantasyCalc -> DB rows
    # ------------------------------------

    for fc in players:
        parsed_pick = parse_fantasycalc_pick(
            source_id=fc.player.sleeperId or "",
            source_name=fc.player.name,
        )

        if parsed_pick is not None:
            season, round_number, slot, is_exact_slot = parsed_pick

            pick_rows.append(
                FantasyCalcPickValue(
                    source_id=fc.player.sleeperId or fc.player.name,
                    source_name=fc.player.name,
                    season=season,
                    round=round_number,
                    slot=slot,
                    is_exact_slot=is_exact_slot,
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
            continue

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

    for row in pick_rows:
        result = await db.execute(
            select(FantasyCalcPickValue).where(
                FantasyCalcPickValue.source_id == row.source_id,
                FantasyCalcPickValue.is_dynasty == row.is_dynasty,
                FantasyCalcPickValue.num_qbs == row.num_qbs,
                FantasyCalcPickValue.num_teams == row.num_teams,
                FantasyCalcPickValue.ppr == row.ppr,
            )
        )

        existing = result.scalar_one_or_none()

        if existing:
            for field in (
                "source_name",
                "season",
                "round",
                "slot",
                "is_exact_slot",
                "value",
                "overall_rank",
                "position_rank",
                "trend_30_day",
                "redraft_value",
                "combined_value",
                "tier",
                "adp",
            ):
                setattr(existing, field, getattr(row, field))

            db.add(existing)
        else:
            db.add(row)


    await db.commit()


    logger.info(
        f"FantasyCalc sync complete "
        f"matched={matched} created={created} updated={updated} "
        f"pick_rows={len(pick_rows)}"
    )


    return {
        "fetched": len(players),
        "matched": matched,
        "pick_rows": len(pick_rows),
        "unmatched": len(unmatched),
        "created": created,
        "updated": updated,
        "unmatched_names": unmatched,
    }
