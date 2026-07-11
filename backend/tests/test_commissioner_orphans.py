from types import SimpleNamespace

from app.schemas.commissioner import CommissionerPlayerAsset
from app.services.commissioner.orphans import (
    build_mock_lineup,
    build_settings_badges,
    get_average_age,
    is_slot_eligible,
)


def test_build_settings_badges_includes_expected_league_summary():
    league = SimpleNamespace(
        total_rosters=12,
        roster_positions=[
            "QB",
            "RB",
            "RB",
            "WR",
            "WR",
            "TE",
            "FLEX",
            "SUPER_FLEX",
            "BN",
            "BN",
        ],
        settings={
            "best_ball": 1,
            "reserve_slots": 2,
            "taxi_slots": 3,
        },
        scoring_settings={
            "rec": 1.5,
            "pass_td": 6,
            "bonus_rec_te": 0.75,
        },
    )

    badges = build_settings_badges(league)

    assert badges == [
        "Best Ball",
        "12 Team",
        "Start 8",
        "15 Roster",
        "SF",
        "1.5 PPR",
        "6 PPTD",
        "0.75 TEP",
    ]


def test_slot_eligibility_supports_dynasty_flex_slots():
    assert is_slot_eligible(slot="SUPER_FLEX", position="QB") is True
    assert is_slot_eligible(slot="FLEX", position="TE") is True
    assert is_slot_eligible(slot="FLEX", position="QB") is False
    assert is_slot_eligible(slot="WR", position="WR") is True
    assert is_slot_eligible(slot="WR", position="RB") is False


def test_build_mock_lineup_assigns_best_player_to_each_starter_slot():
    players = [
        CommissionerPlayerAsset(
            player_id="qb-1",
            name="Elite QB",
            position="QB",
            selected_value=95,
        ),
        CommissionerPlayerAsset(
            player_id="wr-1",
            name="Top WR",
            position="WR",
            selected_value=90,
        ),
        CommissionerPlayerAsset(
            player_id="rb-1",
            name="Top RB",
            position="RB",
            selected_value=80,
        ),
        CommissionerPlayerAsset(
            player_id="te-1",
            name="Top TE",
            position="TE",
            selected_value=70,
        ),
        CommissionerPlayerAsset(
            player_id="wr-2",
            name="Bench WR",
            position="WR",
            selected_value=60,
        ),
    ]

    lineup, bench = build_mock_lineup(
        roster_positions=["QB", "WR", "FLEX", "SUPER_FLEX", "BN"],
        players=players,
    )

    assert [slot.slot for slot in lineup] == [
        "QB",
        "WR",
        "FLEX",
        "SFLEX",
    ]
    assert [slot.player.name if slot.player else None for slot in lineup] == [
        "Elite QB",
        "Top WR",
        "Top RB",
        "Top TE",
    ]
    assert [player.name for player in bench] == [
        "Bench WR",
    ]


def test_get_average_age_rounds_to_one_decimal():
    players = [
        CommissionerPlayerAsset(
            player_id="1",
            name="One",
            age=24.1,
        ),
        CommissionerPlayerAsset(
            player_id="2",
            name="Two",
            age=25.2,
        ),
        CommissionerPlayerAsset(
            player_id="3",
            name="Three",
            age=None,
        ),
    ]

    assert get_average_age(players) == 24.6
    assert get_average_age([]) is None
