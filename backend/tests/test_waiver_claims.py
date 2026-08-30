import pytest
from fastapi import HTTPException

from app.models.db.sleeper.api import League, Roster
from app.schemas.waivers import WaiverClaimRequest
from app.services.waivers.claims import validate_claim


def test_drop_only_claim_succeeds_when_over_capacity():
    league = League(
        league_id="league-1",
        name="Test League",
        season="2026",
        status="in_season",
        total_rosters=12,
        draft_id="draft-1",
        roster_positions=[
            "QB",
            "RB",
            "WR",
            "TE",
            "FLEX",
            "BN",
            "BN",
        ],
        settings={
            "type": 2,
            "best_ball": 0,
            "reserve_slots": 0,
            "taxi_slots": 0,
        },
        scoring_settings={},
    )
    # Roster capacity is 7. Put 8 players on the roster to make it over capacity.
    roster = Roster(
        roster_id=1,
        league_id="league-1",
        owner_id="user-1",
        players=[str(index) for index in range(8)],
        reserve=[],
        taxi=[],
        settings={
            "waiver_budget_used": 0,
        },
    )

    # Confirm the roster is over capacity
    assert roster.open_roster_spots(league) == -1

    # Create a drop-only claim
    claim = WaiverClaimRequest(
        league_id="league-1",
        roster_id=1,
        drop_player_id="0",
        add_player_id=None,
        bid=0,
    )

    # This should not raise an HTTPException
    validate_claim(claim=claim, roster=roster, league=league)


def test_add_drop_claim_fails_when_over_capacity():
    league = League(
        league_id="league-1",
        name="Test League",
        season="2026",
        status="in_season",
        total_rosters=12,
        draft_id="draft-1",
        roster_positions=[
            "QB",
            "RB",
            "WR",
            "TE",
            "FLEX",
            "BN",
            "BN",
        ],
        settings={
            "type": 2,
            "best_ball": 0,
            "reserve_slots": 0,
            "taxi_slots": 0,
        },
        scoring_settings={},
    )
    # Roster capacity is 7. Put 8 players on the roster to make it over capacity.
    roster = Roster(
        roster_id=1,
        league_id="league-1",
        owner_id="user-1",
        players=[str(index) for index in range(8)],
        reserve=[],
        taxi=[],
        settings={
            "waiver_budget_used": 0,
        },
    )

    assert roster.open_roster_spots(league) == -1

    claim = WaiverClaimRequest(
        league_id="league-1",
        roster_id=1,
        drop_player_id="0",
        add_player_id="100",
        bid=0,
    )

    with pytest.raises(HTTPException) as exc:
        validate_claim(claim=claim, roster=roster, league=league)
    
    assert exc.value.status_code == 400
    assert "over its allowed roster capacity" in str(exc.value.detail)

