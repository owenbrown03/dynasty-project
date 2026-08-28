"""One-off import of position ranks from a CSV export into personal projections.

Usage:
    docker cp scripts/personal-ranks-data.csv <api-container>:/tmp/data.csv
    docker compose exec api bash -c "cd /workspace/backend && \
        PYTHONPATH=/workspace/backend python /tmp/import_personal_ranks.py"

Copy this file into the api container first (docker cp), or run it from
a path the container can see. Expects CSV columns: sleeper ID, player,
yr 1, probability 1st outcome, yr 2+ 1st outcome position rank,
probability 2nd outcome, yr 2+ 2nd outcome position rank.

Semantics (owner-confirmed): yr 1 rank becomes the current-season
single outcome; both yr 2+ outcomes apply to EVERY projected future
season; half ranks round half-up; rows overwrite existing projections.
Update SITE_USER_ID below to the account resolved from an actual
usersession row (see AGENTS.md - never assume sleeperconnection).
"""
import asyncio
import csv
import sys
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.crud.sleeper.personal import upsert_personal_projection
from app.models.db.sleeper.api import Player
from app.services.personal_value_projections import (
    get_projection_end_season,
)

SITE_USER_ID = UUID("1f6175f2-16fb-4f85-b57f-32dae8a4eb2c")
BASE_SEASON = 2026
CSV_PATH = "/tmp/data.csv"


def round_half_up(value) -> int:
    return int(Decimal(str(value)).quantize(0, rounding=ROUND_HALF_UP))


def parse_prob(value) -> float:
    raw = str(value).strip().replace("%", "")
    return float(raw)


async def main() -> None:
    rows = list(csv.DictReader(open(CSV_PATH)))
    print(f"csv rows: {len(rows)}")

    async with AsyncSessionLocal() as db:
        player_ids = [
            str(r["sleeper ID"]).strip()
            for r in rows
            if str(r["sleeper ID"]).strip()
        ]
        result = await db.execute(
            select(Player).where(Player.player_id.in_(player_ids))
        )
        players = {p.player_id: p for p in result.scalars().all()}

        all_players = (await db.execute(select(Player))).scalars().all()
        by_name: dict[str, list] = {}
        for p in all_players:
            by_name.setdefault(p.full_name.casefold(), []).append(p)

        print(f"players matched by id: {len(players)} of {len(rows)} rows")

        updated = 0
        skipped_missing = 0
        ambiguous_names = []
        unmatched_names = []

        for row in rows:
            pid = str(row["sleeper ID"]).strip()
            if pid:
                player = players.get(pid)
            else:
                candidates = by_name.get(
                    str(row["player"]).strip().casefold(),
                    [],
                )
                if len(candidates) == 1:
                    player = candidates[0]
                elif len(candidates) > 1:
                    ambiguous_names.append(row["player"])
                    continue
                else:
                    unmatched_names.append(row["player"])
                    continue

            if player is None:
                skipped_missing += 1
                continue

            yr1_rank = round_half_up(row["yr 1"])
            p1 = parse_prob(row["probability 1st outcome"])
            rank1 = round_half_up(row["yr 2+ 1st outcome position rank"])
            p2 = parse_prob(row["probability 2nd outcome"])
            rank2 = round_half_up(row["yr 2+ 2nd outcome position rank"])

            age = None
            if player.birth_date:
                from datetime import date

                born = date.fromisoformat(
                    str(player.birth_date)[:10],
                )
                today = date.today()
                age = (
                    today.year
                    - born.year
                    - ((today.month, today.day) < (born.month, born.day))
                )

            end_season = get_projection_end_season(
                base_season=BASE_SEASON,
                age=age,
                position=player.position,
            )

            await upsert_personal_projection(
                db=db,
                site_user_id=SITE_USER_ID,
                player_id=player.player_id,
                season=BASE_SEASON,
                position=player.position,
                default_source="underdog",
                is_customized=True,
                outcomes=[(yr1_rank, 100.0)],
            )

            for season in range(BASE_SEASON + 1, end_season + 1):
                await upsert_personal_projection(
                    db=db,
                    site_user_id=SITE_USER_ID,
                    player_id=player.player_id,
                    season=season,
                    position=player.position,
                    default_source="underdog",
                    is_customized=True,
                    outcomes=[(rank1, p1), (rank2, p2)],
                )

            updated += 1
            if updated % 100 == 0:
                print(f"progress: {updated}")

        print(
            f"done. players_updated={updated} "
            f"skipped_no_player={skipped_missing}"
        )
        print(f"unmatched names: {len(unmatched_names)}")
        for n in unmatched_names[:20]:
            print("  ?", n)
        print(f"ambiguous names (multi-match): {len(ambiguous_names)}")
        for n in ambiguous_names[:20]:
            print("  ~", n)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
