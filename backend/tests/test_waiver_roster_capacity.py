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


def test_best_ball_occupied_reserve_slots_do_not_expand_claim_capacity():
    league = League(
        league_id="league-best-ball-occupied",
        name="Best Ball With IR",
        season="2026",
        status="in_season",
        total_rosters=12,
        draft_id="draft-best-ball-occupied",
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
        ],
        settings={
            "type": 2,
            "best_ball": 1,
            "reserve_slots": 2,
            "taxi_slots": 2,
        },
        scoring_settings={},
    )
    roster = Roster(
        roster_id=6,
        league_id="league-best-ball-occupied",
        owner_id="user-6",
        players=[str(index) for index in range(11)],
        reserve=["r1", "r2"],
        taxi=["t1"],
    )

    assert roster.claimable_roster_capacity(league) == 11
    assert roster.open_roster_spots(league) == 0


def test_empty_taxi_and_reserve_slots_do_not_expand_claim_capacity():
    league = League(
        league_id="league-empty-extra-slots",
        name="Lineup With Empty IR",
        season="2026",
        status="in_season",
        total_rosters=12,
        draft_id="draft-empty-extra-slots",
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
        roster_id=7,
        league_id="league-empty-extra-slots",
        owner_id="user-7",
        players=[str(index) for index in range(12)],
        reserve=[],
        taxi=[],
    )

    assert roster.claimable_roster_capacity(league) == 12
    assert roster.open_roster_spots(league) == 0


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
