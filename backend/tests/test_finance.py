from types import SimpleNamespace

from app.services.finance import (
    build_seed_finish_probabilities,
    calculate_expected_winnings_from_seed,
    calculate_rank,
)


def test_calculate_rank_uses_all_rosters_in_league():
    rosters = [
        SimpleNamespace(
            roster_id=1,
            wins=2,
            losses=1,
            ties=0,
            fpts=300.0,
        ),
        SimpleNamespace(
            roster_id=2,
            wins=3,
            losses=0,
            ties=0,
            fpts=250.0,
        ),
        SimpleNamespace(
            roster_id=3,
            wins=1,
            losses=2,
            ties=0,
            fpts=350.0,
        ),
    ]

    assert calculate_rank(
        rosters=rosters,
        roster_id=1,
    ) == 2


def test_seed_finish_probabilities_sum_to_one():
    probabilities = build_seed_finish_probabilities(
        seed=2,
        total_rosters=12,
        playoff_teams=6,
    )

    assert round(
        sum(probabilities.values()),
        6,
    ) == 1
    assert probabilities[2] > probabilities[1]
    assert probabilities[2] > probabilities[6]


def test_expected_winnings_uses_seed_probability_curve():
    expected = calculate_expected_winnings_from_seed(
        payout_structure={
            "1": 200.0,
            "2": 75.0,
            "3": 25.0,
        },
        projected_seed=2,
        total_rosters=12,
        playoff_teams=6,
    )

    assert expected is not None
    assert 25 < expected < 200
