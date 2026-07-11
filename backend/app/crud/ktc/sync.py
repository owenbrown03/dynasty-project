import logging
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.sleeper.api import Player
from app.models.db.ktc.models import KTCPlayerMap, KTCValue, KTCPickValue
from app.integrations.ktc import KTCClient
from app.services.draft.values import parse_ktc_pick_name
from app.services.sleeper.normalize import SleeperNameIndex

logger = logging.getLogger(__name__)


async def sync_ktc_values(
    db: AsyncSession,
    ktc: KTCClient,
    *,
    include_redraft: bool = False,
) -> dict:
    """
    Pulls KTC dynasty (and optionally redraft) values, matches each player
    to our canonical Sleeper player_id, and upserts KTCPlayerMap + KTCValue.
    """

    logger.info("Starting KTC value sync")

    # --------------------------------------------------
    # 1. Build the Sleeper name index from our own DB
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
    # 2. Pull KTC rankings (HTML scrape under the hood)
    # --------------------------------------------------
    ktc_players = await ktc.read.get_dynasty_rankings(include_redraft=include_redraft)
    logger.info(f"Scraped {len(ktc_players)} KTC players")

    # --------------------------------------------------
    # 3. Load existing maps
    # --------------------------------------------------
    result = await db.execute(select(KTCPlayerMap))
    existing_maps = {m.ktc_name: m for m in result.scalars().all()}

    matched = 0
    unmatched: list[str] = []
    new_maps = []
    new_value_rows = []
    pick_rows = []

    for ktc_player in ktc_players:
        parsed_pick = parse_ktc_pick_name(
            ktc_player.player_name,
        )

        if parsed_pick is not None:
            season, round_number, bucket = parsed_pick
            pick_rows.append(
                KTCPickValue(
                    source_name=ktc_player.player_name,
                    season=season,
                    round=round_number,
                    bucket=bucket,
                    value=ktc_player.value,
                    sf_value=ktc_player.sf_value,
                )
            )
            continue

        existing = existing_maps.get(ktc_player.player_name)

        if existing:
            player_id = existing.player_id
        else:
            player_id, matched_via, confidence = name_index.match(
                ktc_player.player_name,
                team=ktc_player.team or "",
            )

            if not player_id:
                unmatched.append(f"{ktc_player.player_name} ({ktc_player.team}) value {ktc_player.value}")
                continue

            new_maps.append(
                KTCPlayerMap(
                    ktc_name=ktc_player.player_name,
                    player_id=player_id,
                    matched_via=matched_via,
                    confidence=confidence,
                )
            )

        matched += 1

        new_value_rows.append(
            KTCValue(
                player_id=player_id,
                value=ktc_player.value,
                position_rank=ktc_player.position_rank,
                sf_value=ktc_player.sf_value,
                sf_position_rank=ktc_player.sf_position_rank,
                redraft_value=ktc_player.redraft_value,
                redraft_position_rank=ktc_player.redraft_position_rank,
                sf_redraft_value=ktc_player.sf_redraft_value,
                sf_redraft_position_rank=ktc_player.sf_redraft_position_rank,
            )
        )

    logger.info(f"Matched: {matched}/{len(ktc_players)}")
    if unmatched:
        logger.info(f"Unmatched ({len(unmatched)}):\n" + "\n".join(f"  {u}" for u in unmatched))

    # --------------------------------------------------
    # 4. Persist
    # --------------------------------------------------
    for m in new_maps:
        db.add(m)

    for row in new_value_rows:
        existing_value = await db.execute(
            select(KTCValue).where(KTCValue.player_id == row.player_id)
        )
        existing_row = existing_value.scalar_one_or_none()
        if existing_row:
            existing_row.value = row.value
            existing_row.position_rank = row.position_rank
            existing_row.sf_value = row.sf_value
            existing_row.sf_position_rank = row.sf_position_rank
            existing_row.redraft_value = row.redraft_value
            existing_row.redraft_position_rank = row.redraft_position_rank
            existing_row.sf_redraft_value = row.sf_redraft_value
            existing_row.sf_redraft_position_rank = row.sf_redraft_position_rank
            db.add(existing_row)
        else:
            db.add(row)

    for row in pick_rows:
        existing_pick = await db.execute(
            select(KTCPickValue).where(
                KTCPickValue.season == row.season,
                KTCPickValue.round == row.round,
                KTCPickValue.bucket == row.bucket,
            )
        )
        existing_pick_row = existing_pick.scalar_one_or_none()

        if existing_pick_row:
            existing_pick_row.source_name = row.source_name
            existing_pick_row.value = row.value
            existing_pick_row.sf_value = row.sf_value
            db.add(existing_pick_row)
        else:
            db.add(row)

    await db.commit()

    return {
        "fetched": len(ktc_players),
        "matched": matched,
        "pick_rows": len(pick_rows),
        "unmatched": len(unmatched),
        "unmatched_names": unmatched,
        "new_maps_created": len(new_maps),
    }
