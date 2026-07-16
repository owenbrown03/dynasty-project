from app.models.db.sleeper.api import League, Roster


def test_best_ball_empty_reserve_slots_do_not_expand_claim_capacity():
    league = League(
        league_id="league-1",
        name="BestBall, This Is",
        season="2026",
        status="in_season",
        total_rosters=12,
        draft_id="draft-1",
        roster_positions=[
            "QB",
            "RB",
            "RB",
            "WR",
            "WR",
            "TE",
            "FLEX",
            "FLEX",
            "FLEX",
            "FLEX",
            "SUPER_FLEX",
            "BN",
            "BN",
            "BN",
            "BN",
            "BN",
            "BN",
            "BN",
            "BN",
            "BN",
            "BN",
            "BN",
            "BN",
            "BN",
            "BN",
        ],
        settings={
            "type": 2,
            "best_ball": 1,
            "reserve_slots": 2,
            "taxi_slots": 0,
        },
        scoring_settings={},
    )
    roster = Roster(
        roster_id=4,
        league_id="league-1",
        owner_id="user-1",
        players=[str(index) for index in range(26)],
        reserve=[],
        taxi=[],
    )

    assert roster.claimable_roster_capacity(league) == 25
    assert roster.open_roster_spots(league) == -1


def test_occupied_taxi_and_reserve_slots_expand_claim_capacity():
    league = League(
        league_id="league-2",
        name="Taxi League",
        season="2026",
        status="in_season",
        total_rosters=12,
        draft_id="draft-2",
        roster_positions=[
            "QB",
            "RB",
            "RB",
            "WR",
            "WR",
            "TE",
            "FLEX",
            "FLEX",
            "SUPER_FLEX",
            "BN",
            "BN",
            "BN",
            "BN",
            "BN",
            "BN",
            "BN",
            "BN",
            "BN",
            "BN",
            "BN",
        ],
        settings={
            "type": 2,
            "best_ball": 0,
            "reserve_slots": 3,
            "taxi_slots": 5,
        },
        scoring_settings={},
    )
    roster = Roster(
        roster_id=5,
        league_id="league-2",
        owner_id="user-2",
        players=[str(index) for index in range(24)],
        reserve=["r1", "r2"],
        taxi=["t1", "t2", "t3"],
    )

    assert roster.claimable_roster_capacity(league) == 25
    assert roster.open_roster_spots(league) == 1
