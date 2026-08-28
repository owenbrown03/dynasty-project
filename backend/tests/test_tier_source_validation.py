import asyncio

import pytest
from fastapi import HTTPException

from app.services.values.tiers import load_player_values_for_basis
from app.services.values.basis import ValueBasis


def test_league_context_basis_without_league_is_clean_400():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            load_player_values_for_basis(
                db=object(),
                redis=None,
                value_basis=ValueBasis.MY_ROSTER_WAR,
                league=None,
                season=2026,
            )
        )

    assert exc.value.status_code == 400
    assert "without a league" in exc.value.detail


def test_all_league_context_bases_reject_missing_league():
    bases = [
        ValueBasis.SLEEPER_WAR,
        ValueBasis.MY_WAR,
        ValueBasis.MY_ROSTER_WAR,
        ValueBasis.MY_STARTER_WAR,
        ValueBasis.DYNASTY_ROSTER_WAR,
        ValueBasis.DYNASTY_STARTER_WAR,
        ValueBasis.SLEEPER_PROJECTION,
    ]

    for basis in bases:
        with pytest.raises(HTTPException) as exc:
            asyncio.run(
                load_player_values_for_basis(
                    db=object(),
                    redis=None,
                    value_basis=basis,
                    league=None,
                    season=2026,
                )
            )

        assert exc.value.status_code == 400, basis
