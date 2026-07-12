from __future__ import annotations

from app.schemas.draft import DraftPickAsset
from app.schemas.trades import (
    TradeCalculatorPickValueResponse,
)
from app.services.draft.values import (
    get_resolved_pick_values_by_key,
)
from app.services.values.basis import ValueBasis


async def get_trade_calculator_pick_value(
    db,
    *,
    season: str,
    round_number: int,
    slot: int | None,
    total_rosters: int,
    num_qbs: int,
    ppr: int,
) -> TradeCalculatorPickValueResponse:
    pick = DraftPickAsset(
        season=season,
        round=round_number,
        og_roster_id=1,
        current_owner_roster_id=1,
        slot=slot,
        label=(
            f"{season} Pick {round_number}.{slot:02d}"
            if slot is not None
            else f"{season} Round {round_number}"
        ),
    )

    ktc_values = await get_resolved_pick_values_by_key(
        db,
        picks=[pick],
        value_basis=ValueBasis.KTC,
        league_num_qbs=num_qbs,
        league_total_rosters=total_rosters,
        league_ppr=ppr,
    )
    fc_values = await get_resolved_pick_values_by_key(
        db,
        picks=[pick],
        value_basis=ValueBasis.FANTASYCALC,
        league_num_qbs=num_qbs,
        league_total_rosters=total_rosters,
        league_ppr=ppr,
    )
    key = (
        pick.season,
        pick.round,
        pick.og_roster_id,
    )

    return TradeCalculatorPickValueResponse(
        season=season,
        round=round_number,
        slot=slot,
        total_rosters=total_rosters,
        num_qbs=num_qbs,
        ppr=ppr,
        ktc_value=(
            ktc_values.get(key).value
            if key in ktc_values
            else None
        ),
        fc_value=(
            fc_values.get(key).value
            if key in fc_values
            else None
        ),
    )
