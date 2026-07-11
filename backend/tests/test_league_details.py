from app.services.leagues.details import (
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
