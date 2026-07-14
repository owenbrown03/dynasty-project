import asyncio

from app.schemas.draft import DraftPickAsset
from app.services.draft.values import (
    ResolvedPickValue,
    get_pick_bucket,
    get_resolved_pick_values_by_key,
    parse_fantasycalc_pick,
    parse_ktc_pick_name,
    resolve_ktc_pick_value,
)
from app.services.draft.rookie_war import RookiePickWarAggregate
from app.services.values.basis import ValueBasis
from app.models.db.ktc.models import KTCPickValue


def test_parse_fantasycalc_pick_exact_slot():
    parsed = parse_fantasycalc_pick(
        source_id="DP_0_3",
        source_name="2026 Pick 1.04",
    )

    assert parsed == ("2026", 1, 4, True)


def test_parse_fantasycalc_pick_generic_round():
    parsed = parse_fantasycalc_pick(
        source_id="FP_2027_2",
        source_name="2027 2nd",
    )

    assert parsed == ("2027", 2, None, False)


def test_parse_ktc_pick_name():
    parsed = parse_ktc_pick_name(
        "2028 Late 3rd",
    )

    assert parsed == ("2028", 3, "late")


def test_get_pick_bucket_for_twelve_team_league():
    assert get_pick_bucket(slot=1, total_rosters=12) == "early"
    assert get_pick_bucket(slot=6, total_rosters=12) == "mid"
    assert get_pick_bucket(slot=11, total_rosters=12) == "late"


def test_resolve_ktc_pick_value_defaults_to_mid_without_slot():
    pick = DraftPickAsset(
        season="2026",
        round=1,
        og_roster_id=1,
        current_owner_roster_id=1,
        label="2026 Round 1",
        slot=None,
    )

    rows = [
        KTCPickValue(
            source_name="2026 Early 1st",
            season="2026",
            round=1,
            bucket="early",
            value=6000,
            sf_value=5500,
        ),
        KTCPickValue(
            source_name="2026 Mid 1st",
            season="2026",
            round=1,
            bucket="mid",
            value=5000,
            sf_value=4607,
        ),
    ]

    resolved = resolve_ktc_pick_value(
        pick=pick,
        total_rosters=12,
        rows=rows,
    )

    assert resolved.value == 4607.0
    assert resolved.source_label == "2026 Mid 1st"


def test_get_resolved_pick_values_supports_rookie_pick_war(
    monkeypatch,
):
    pick = DraftPickAsset(
        season="2027",
        round=1,
        og_roster_id=1,
        current_owner_roster_id=1,
        label="2027 Pick 1.04",
        slot=4,
    )

    async def fake_get_rookie_pick_war_values_by_key(
        db,
        *,
        picks,
        league_total_rosters,
        league_scoring_settings,
        league_roster_positions,
    ):
        del db, league_total_rosters, league_scoring_settings, league_roster_positions
        return {
            (
                picks[0].season,
                picks[0].round,
                picks[0].og_roster_id,
            ): RookiePickWarAggregate(
                starter_war=5.1,
                roster_war=8.4,
                sample_size=12,
                source_label="Historical rookie WAR from 12 past 1.04 outcomes",
            )
        }

    monkeypatch.setattr(
        "app.services.draft.values.get_rookie_pick_war_values_by_key",
        fake_get_rookie_pick_war_values_by_key,
    )

    resolved = asyncio.run(
        get_resolved_pick_values_by_key(
            db=None,
            picks=[pick],
            value_basis=ValueBasis.ROOKIE_PICK_WAR,
            league_num_qbs=2,
            league_total_rosters=12,
            league_ppr=1,
            league_scoring_settings={"rec": 1.0},
            league_roster_positions=["QB", "RB", "WR", "TE", "FLEX"],
        )
    )

    assert resolved == {
        ("2027", 1, 1): ResolvedPickValue(
            value=8.4,
            source_label="Historical rookie WAR from 12 past 1.04 outcomes",
        )
    }
