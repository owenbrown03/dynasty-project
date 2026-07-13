from app.models.db.sleeper.api import League, Roster
from app.schemas.draft import DraftPickAsset
from app.services.draft.projection import (
    build_projected_pick_slots_by_roster_id,
)
from app.services.draft.values import (
    get_effective_pick_slot,
)


def test_build_projected_pick_slots_defaults_to_max_pf():
    league = League(
        league_id="league-1",
        name="Test",
        season="2026",
        status="in_season",
        total_rosters=3,
        draft_id="draft-1",
        settings={"type": 2},
        scoring_settings={},
        roster_positions=["QB", "RB", "WR", "TE", "FLEX"],
    )
    rosters = [
        Roster(
            roster_id=1,
            league_id="league-1",
            settings={"wins": 5, "losses": 1, "fpts": 800, "ppts": 900},
        ),
        Roster(
            roster_id=2,
            league_id="league-1",
            settings={"wins": 2, "losses": 4, "fpts": 700, "ppts": 650},
        ),
        Roster(
            roster_id=3,
            league_id="league-1",
            settings={"wins": 2, "losses": 4, "fpts": 760, "ppts": 700},
        ),
    ]

    result = build_projected_pick_slots_by_roster_id(
        league=league,
        rosters=rosters,
        current_week=6,
        projected_points_by_roster_id={
            1: 150,
            2: 120,
            3: 145,
        },
    )

    assert result.method_used == "max_pf"
    assert result.slots_by_roster_id == {
        2: 1,
        3: 2,
        1: 3,
    }


def test_get_effective_pick_slot_prefers_actual_slot():
    pick = DraftPickAsset(
        season="2027",
        round=1,
        og_roster_id=1,
        current_owner_roster_id=1,
        slot=4,
        projected_slot=2,
        label="2027 Pick 1.04",
    )

    assert get_effective_pick_slot(pick) == 4


def test_get_effective_pick_slot_uses_projected_slot_when_needed():
    pick = DraftPickAsset(
        season="2027",
        round=1,
        og_roster_id=1,
        current_owner_roster_id=1,
        slot=None,
        projected_slot=2,
        label="2027 Pick 1.02 (proj.)",
    )

    assert get_effective_pick_slot(pick) == 2
