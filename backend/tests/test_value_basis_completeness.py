"""Every value basis must be fully supported - no silent fall-through.

These tests exist because sleeper_projection (and later the my_*
variants) reached production with no get_player_value case: the tier
board silently served empty tiers. Any new ValueBasis member now
fails this suite until it is classified in VALUE_BASIS_SPECS and
resolves a number from a populated PlayerValue.
"""
import pytest

from app.schemas.player import PlayerValue
from app.services.values.basis import (
    get_player_value,
    VALUE_BASIS_SPECS,
    ValueBasis,
    ValueBasisSpec,
)
from app.services.values.war_settings import (
    normalize_war_value_settings,
)


FULLY_POPULATED_PLAYER = PlayerValue(
    player_id="1",
    name="Test Player",
    position="RB",
    team="TST",
    age=25.0,
    ktc_value=5000,
    fc_value=4800,
    adp_value=120.5,
    projected_points=280.5,
    redraft_starter_war=4.2,
    redraft_roster_war=6.1,
    dynasty_starter_war=9.3,
    dynasty_roster_war=14.7,
    my_dynasty_starter_war=8.8,
    my_dynasty_roster_war=13.9,
)


def test_every_value_basis_is_classified():
    missing = [
        basis
        for basis in ValueBasis
        if basis not in VALUE_BASIS_SPECS
    ]

    assert missing == [], (
        f"ValueBasis members missing from VALUE_BASIS_SPECS: "
        f"{missing}. Add a spec describing the basis's needs."
    )


def test_specs_only_use_known_flags():
    for basis, spec in VALUE_BASIS_SPECS.items():
        assert isinstance(spec, ValueBasisSpec), basis


@pytest.mark.parametrize(
    "basis",
    [
        basis
        for basis in ValueBasis
        if basis != ValueBasis.ROOKIE_PICK_WAR
    ],
)
def test_every_basis_resolves_a_number(basis):
    """ROOKIE_PICK_WAR is intentionally None for player rows (it
    prices picks, not players); every other basis must resolve."""
    value = get_player_value(
        FULLY_POPULATED_PLAYER,
        basis,
        normalize_war_value_settings(None),
    )

    assert value is not None, (
        f"{basis} returned None for a fully populated PlayerValue - "
        "get_player_value is missing a case."
    )


def test_league_context_flag_matches_reality():
    # Market bases resolve without a league; everything else needs
    # the league's redraft context.
    assert (
        not VALUE_BASIS_SPECS[ValueBasis.KTC].needs_league_context
    )
    assert (
        not VALUE_BASIS_SPECS[
            ValueBasis.FANTASYCALC
        ].needs_league_context
    )
    assert VALUE_BASIS_SPECS[
        ValueBasis.SLEEPER_PROJECTION
    ].needs_league_context
