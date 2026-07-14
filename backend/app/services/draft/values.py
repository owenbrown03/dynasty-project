from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.fc.picks import get_fantasycalc_pick_values
from app.crud.ktc.picks import get_ktc_pick_values
from app.models.db.fc.models import FantasyCalcPickValue
from app.models.db.ktc.models import KTCPickValue
from app.schemas.draft import DraftPickAsset
from app.services.draft.rookie_war import (
    get_rookie_pick_war_values_by_key,
)
from app.services.values.basis import ValueBasis


@dataclass(frozen=True)
class ResolvedPickValue:
    value: float | None
    source_label: str | None = None


def get_effective_pick_slot(
    pick: DraftPickAsset,
) -> int | None:
    return (
        pick.slot
        if pick.slot is not None
        else pick.projected_slot
    )


def get_pick_bucket(
    *,
    slot: int,
    total_rosters: int,
) -> str:
    if total_rosters <= 0:
        return "mid"

    early_cutoff = -(-total_rosters // 3)
    mid_cutoff = -(-(2 * total_rosters) // 3)

    if slot <= early_cutoff:
        return "early"

    if slot <= mid_cutoff:
        return "mid"

    return "late"


def parse_ktc_pick_name(
    name: str,
) -> tuple[str, int, str] | None:
    match = re.fullmatch(
        r"(\d{4})\s+(Early|Mid|Late)\s+(\d+)(?:st|nd|rd|th)",
        name.strip(),
        re.IGNORECASE,
    )

    if match is None:
        return None

    season, bucket, round_number = match.groups()
    return season, int(round_number), bucket.lower()


def parse_fantasycalc_pick(
    *,
    source_id: str,
    source_name: str,
) -> tuple[str, int, int | None, bool] | None:
    exact_id_match = re.fullmatch(
        r"DP_(\d+)_(\d+)",
        source_id.strip(),
    )
    exact_name_match = re.fullmatch(
        r"(\d{4})\s+Pick\s+(\d+)\.(\d+)",
        source_name.strip(),
        re.IGNORECASE,
    )

    if exact_id_match and exact_name_match:
        season, round_number, slot = exact_name_match.groups()
        return season, int(round_number), int(slot), True

    generic_id_match = re.fullmatch(
        r"FP_(\d{4})_(\d+)",
        source_id.strip(),
    )
    generic_name_match = re.fullmatch(
        r"(\d{4})\s+(\d+)(?:st|nd|rd|th)",
        source_name.strip(),
        re.IGNORECASE,
    )

    if generic_id_match:
        season, round_number = generic_id_match.groups()
        return season, int(round_number), None, False

    if generic_name_match:
        season, round_number = generic_name_match.groups()
        return season, int(round_number), None, False

    return None


def resolve_fantasycalc_pick_value(
    *,
    pick: DraftPickAsset,
    rows: list[FantasyCalcPickValue],
) -> ResolvedPickValue:
    if not rows:
        return ResolvedPickValue(value=None)

    exact_by_slot = {
        row.slot: row
        for row in rows
        if row.is_exact_slot and row.slot is not None
    }

    effective_slot = get_effective_pick_slot(
        pick,
    )

    if (
        effective_slot is not None
        and effective_slot in exact_by_slot
    ):
        exact = exact_by_slot[effective_slot]
        return ResolvedPickValue(
            value=float(exact.value),
            source_label=exact.source_name,
        )

    generic = next(
        (
            row
            for row in rows
            if not row.is_exact_slot
        ),
        None,
    )

    if generic is None:
        return ResolvedPickValue(value=None)

    return ResolvedPickValue(
        value=float(generic.value),
        source_label=generic.source_name,
    )


def resolve_ktc_pick_value(
    *,
    pick: DraftPickAsset,
    total_rosters: int,
    rows: list[KTCPickValue],
) -> ResolvedPickValue:
    if not rows:
        return ResolvedPickValue(value=None)

    effective_slot = get_effective_pick_slot(
        pick,
    )

    bucket = (
        get_pick_bucket(
            slot=effective_slot,
            total_rosters=total_rosters,
        )
        if effective_slot is not None
        else "mid"
    )

    row = next(
        (
            candidate
            for candidate in rows
            if candidate.bucket == bucket
        ),
        None,
    )

    if row is None and bucket != "mid":
        row = next(
            (
                candidate
                for candidate in rows
                if candidate.bucket == "mid"
            ),
            None,
        )

    if row is None:
        return ResolvedPickValue(value=None)

    return ResolvedPickValue(
        value=float(
            row.sf_value
            if row.sf_value is not None
            else row.value
        ),
        source_label=row.source_name,
    )


async def get_resolved_pick_values_by_key(
    db: AsyncSession,
    *,
    picks: list[DraftPickAsset],
    value_basis: ValueBasis,
    league_num_qbs: int,
    league_total_rosters: int,
    league_ppr: int,
    league_scoring_settings: dict[str, float] | None = None,
    league_roster_positions: list[str] | None = None,
) -> dict[tuple[str, int, int], ResolvedPickValue]:
    if value_basis not in {
        ValueBasis.KTC,
        ValueBasis.FANTASYCALC,
        ValueBasis.ROOKIE_PICK_WAR,
    }:
        return {}

    seasons = sorted({pick.season for pick in picks})
    rounds = sorted({pick.round for pick in picks})

    if value_basis == ValueBasis.ROOKIE_PICK_WAR:
        if (
            league_scoring_settings is None
            or league_roster_positions is None
        ):
            return {}

        rookie_war_values_by_key = (
            await get_rookie_pick_war_values_by_key(
                db,
                picks=picks,
                league_total_rosters=league_total_rosters,
                league_scoring_settings=league_scoring_settings,
                league_roster_positions=league_roster_positions,
            )
        )

        return {
            key: ResolvedPickValue(
                value=aggregate.roster_war,
                source_label=aggregate.source_label,
            )
            for key, aggregate in rookie_war_values_by_key.items()
        }

    if value_basis == ValueBasis.FANTASYCALC:
        rows_by_shape = await get_fantasycalc_pick_values(
            db,
            is_dynasty=True,
            num_qbs=league_num_qbs,
            num_teams=league_total_rosters,
            ppr=league_ppr,
            seasons=seasons,
            rounds=rounds,
        )

        return {
            (
                pick.season,
                pick.round,
                pick.og_roster_id,
            ): resolve_fantasycalc_pick_value(
                pick=pick,
                rows=rows_by_shape.get(
                    (pick.season, pick.round),
                    [],
                ),
            )
            for pick in picks
        }

    rows_by_shape = await get_ktc_pick_values(
        db,
        seasons=seasons,
        rounds=rounds,
    )

    return {
        (
            pick.season,
            pick.round,
            pick.og_roster_id,
        ): resolve_ktc_pick_value(
            pick=pick,
            total_rosters=league_total_rosters,
            rows=rows_by_shape.get(
                (pick.season, pick.round),
                [],
            ),
        )
        for pick in picks
    }
