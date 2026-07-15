from types import SimpleNamespace

from app.services.leagues.details import (
    build_league_roster_construction_targets,
    calculate_projected_starter_points,
    is_slot_eligible,
)
from app.services.leagues.models import LeaguePlayer


def test_is_slot_eligible_supports_real_sleeper_flex_slots():
    assert is_slot_eligible("REC_FLEX", "WR") is True
    assert is_slot_eligible("WRRB_FLEX", "RB") is True
    assert is_slot_eligible("IDP_FLEX", "LB") is True
    assert is_slot_eligible("IDP_FLEX", "WR") is False


def test_calculate_projected_starter_points_uses_best_valid_lineup():
    players = [
        LeaguePlayer(
            player_id="qb-1",
            name="QB One",
            position="QB",
            projected_points=320,
        ),
        LeaguePlayer(
            player_id="rb-1",
            name="RB One",
            position="RB",
            projected_points=220,
        ),
        LeaguePlayer(
            player_id="wr-1",
            name="WR One",
            position="WR",
            projected_points=210,
        ),
        LeaguePlayer(
            player_id="te-1",
            name="TE One",
            position="TE",
            projected_points=150,
        ),
        LeaguePlayer(
            player_id="wr-2",
            name="WR Two",
            position="WR",
            projected_points=180,
        ),
    ]

    total = calculate_projected_starter_points(
        roster_positions=["QB", "RB", "WR", "REC_FLEX"],
        players=players,
    )

    assert total == 930.0


def test_build_league_roster_construction_targets_is_shared_and_exact():
    league = SimpleNamespace(
        roster_positions=[
            "QB",
            "RB",
            "WR",
            "TE",
            "FLEX",
            "FLEX",
            "BN",
            "BN",
            "BN",
            "BN",
        ],
    )
    roster_rows = [
        SimpleNamespace(
            players=["a"] * 10,
            open_roster_spots=lambda _: 0,
        ),
        SimpleNamespace(
            players=["b"] * 10,
            open_roster_spots=lambda _: 0,
        ),
    ]
    seasonal_results = [
        [
            SimpleNamespace(position="QB", redraft_roster_war=10.0),
            SimpleNamespace(position="QB", redraft_roster_war=8.0),
            SimpleNamespace(position="QB", redraft_roster_war=6.0),
            SimpleNamespace(position="RB", redraft_roster_war=9.0),
            SimpleNamespace(position="RB", redraft_roster_war=8.0),
            SimpleNamespace(position="RB", redraft_roster_war=7.0),
            SimpleNamespace(position="RB", redraft_roster_war=6.0),
            SimpleNamespace(position="WR", redraft_roster_war=9.5),
            SimpleNamespace(position="WR", redraft_roster_war=8.5),
            SimpleNamespace(position="WR", redraft_roster_war=7.5),
            SimpleNamespace(position="WR", redraft_roster_war=6.5),
            SimpleNamespace(position="TE", redraft_roster_war=4.0),
            SimpleNamespace(position="TE", redraft_roster_war=2.0),
        ],
        [
            SimpleNamespace(position="QB", redraft_roster_war=9.0),
            SimpleNamespace(position="QB", redraft_roster_war=7.0),
            SimpleNamespace(position="QB", redraft_roster_war=5.0),
            SimpleNamespace(position="RB", redraft_roster_war=10.0),
            SimpleNamespace(position="RB", redraft_roster_war=9.0),
            SimpleNamespace(position="RB", redraft_roster_war=8.0),
            SimpleNamespace(position="RB", redraft_roster_war=7.0),
            SimpleNamespace(position="WR", redraft_roster_war=9.0),
            SimpleNamespace(position="WR", redraft_roster_war=8.0),
            SimpleNamespace(position="WR", redraft_roster_war=7.0),
            SimpleNamespace(position="WR", redraft_roster_war=6.0),
            SimpleNamespace(position="TE", redraft_roster_war=3.0),
            SimpleNamespace(position="TE", redraft_roster_war=1.0),
        ],
    ]

    targets = build_league_roster_construction_targets(
        league=league,
        roster_rows=roster_rows,
        seasonal_results=seasonal_results,
    )

    assert [target.target_count for target in targets] == [2, 4, 3, 1]
    assert sum(target.target_count for target in targets) == 10
    assert round(sum(target.war_share for target in targets), 1) == 99.9
