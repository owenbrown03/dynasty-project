import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.analytics.war.consensus_rookie_drafts import (
    FANTASYCALC_CONSENSUS_ROOKIE_DRAFTS,
)
from app.services.draft.rookie_war import (
    DEFAULT_SUPERFLEX_PPR_SETTINGS,
    get_rookie_pick_war_values_by_key,
    get_rookie_war_history,
)


def test_consensus_rookie_drafts_integrity():
    # 7 draft classes: 2020 through 2026
    seasons = sorted({row[0] for row in FANTASYCALC_CONSENSUS_ROOKIE_DRAFTS})
    assert seasons == [2020, 2021, 2022, 2023, 2024, 2025, 2026]

    # Exactly 48 picks per season (4 rounds * 12 slots)
    for s in seasons:
        season_picks = [row for row in FANTASYCALC_CONSENSUS_ROOKIE_DRAFTS if row[0] == s]
        assert len(season_picks) == 48, f"Season {s} has {len(season_picks)} picks instead of 48"

        # Unique round + slot
        slots = {(row[1], row[2]) for row in season_picks}
        assert len(slots) == 48


def test_rookie_war_history_default_superflex(monkeypatch):
    class FakeLoader:
        async def get_season_stats(self, db, season):
            return [SimpleNamespace(player_id="6770")]

    class FakeWarService:
        def __init__(self):
            self.loader = FakeLoader()

        async def calculate_with_data(self, league, shared):
            assert league.scoring_settings == DEFAULT_SUPERFLEX_PPR_SETTINGS["scoring_settings"]
            assert league.total_rosters == 12
            return [
                SimpleNamespace(
                    player_id="6770",
                    starter_war=0.8,
                    roster_war=1.2,
                )
            ]

    monkeypatch.setattr(
        "app.services.draft.rookie_war._get_cached_players",
        AsyncMock(return_value={"6770": SimpleNamespace(full_name="Joe Burrow", position="QB", team="CIN")}),
    )
    monkeypatch.setattr(
        "app.services.draft.rookie_war._war_service",
        FakeWarService(),
    )
    monkeypatch.setattr(
        "app.services.draft.rookie_war.get_available_stat_seasons",
        AsyncMock(return_value=[2020, 2021, 2022, 2023, 2024, 2025]),
    )

    rows = asyncio.run(
        get_rookie_war_history(
            db=None,
            redis=None,
            league=None,
            rounds=[1],
        )
    )

    assert len(rows) == 7 * 12  # 7 draft classes * 12 picks in round 1
    burrow_row = next((r for r in rows if r["draft_year"] == 2020 and r["round_slot"] == 1), None)
    assert burrow_row is not None
    assert burrow_row["name"] == "Joe Burrow"
    assert burrow_row["position"] == "QB"
    # 6 active seasons * 0.8 starter WAR = 4.80
    assert burrow_row["starter_war"] == 4.8


def test_rookie_war_history_custom_league(monkeypatch):
    custom_scoring = {"pass_td": 6.0, "rec": 1.5}
    league = SimpleNamespace(
        league_id="custom-123",
        scoring_settings=custom_scoring,
        roster_positions=["QB", "RB", "WR", "TE", "SUPER_FLEX"],
        total_rosters=10,
    )

    class FakeLoader:
        async def get_season_stats(self, db, season):
            return [SimpleNamespace(player_id="6770")]

    class FakeWarService:
        def __init__(self):
            self.loader = FakeLoader()

        async def calculate_with_data(self, league, shared):
            assert league.scoring_settings == custom_scoring
            assert league.total_rosters == 10
            return [
                SimpleNamespace(
                    player_id="6770",
                    starter_war=1.1,
                    roster_war=1.5,
                )
            ]

    monkeypatch.setattr(
        "app.services.draft.rookie_war._get_cached_players",
        AsyncMock(return_value={"6770": SimpleNamespace(full_name="Joe Burrow", position="QB", team="CIN")}),
    )
    monkeypatch.setattr(
        "app.services.draft.rookie_war._war_service",
        FakeWarService(),
    )
    monkeypatch.setattr(
        "app.services.draft.rookie_war.get_available_stat_seasons",
        AsyncMock(return_value=[2020, 2021]),
    )

    rows = asyncio.run(
        get_rookie_war_history(
            db=None,
            redis=None,
            league=league,
            rounds=[1],
        )
    )

    burrow_row = next((r for r in rows if r["draft_year"] == 2020 and r["round_slot"] == 1), None)
    assert burrow_row is not None
    # 6 active seasons (2020-2025) * 1.1 = 6.6
    assert burrow_row["starter_war"] == 6.6


def test_smooth_rookie_war_curve_monotonicity():
    from app.services.draft.rookie_war import smooth_rookie_war_curve

    # Simulating raw noisy pick slot averages where 1.11 is artificially higher than 1.10
    noisy_averages = [
        3.0, 1.2, 1.8, 2.4, 2.1, 1.5, 1.6, 1.5, 1.1, 0.9, 1.9, -0.1,  # Round 1 (1.11 spike = 1.9)
        -0.2, 0.2, 0.3, -0.3, 0.4, 0.4, 0.7, -0.3, -0.4, -0.2, 0.1, -0.7, # Round 2 (2.07 spike = 0.7)
        -0.1, -0.5, -0.7, -0.3, -0.4, -0.1, -0.5, -0.2, -0.7, -0.3, -0.1, -0.3,
        -0.2, 0.1, 0.6, -0.1, -0.4, -0.2, -0.1, -0.1, -0.2, 0.0, 0.0, -0.1,
    ]

    smoothed = smooth_rookie_war_curve(noisy_averages, sigma=2.0, min_decay_slope=0.01)
    assert len(smoothed) == len(noisy_averages)

    # Strictly monotonic decreasing: every higher pick is strictly valued more than the next
    for i in range(len(smoothed) - 1):
        assert smoothed[i] > smoothed[i + 1], f"Monotonicity violated at pick slot index {i}: {smoothed[i]} <= {smoothed[i+1]}"

    # Pick 1.01 must be higher than 1.02, 1.10 must be higher than 1.11
    assert smoothed[0] > smoothed[1]
    assert smoothed[9] > smoothed[10] # 1.10 > 1.11


def test_future_pick_discounting_by_year(monkeypatch):
    import asyncio
    from app.services.draft.rookie_war import get_rookie_pick_war_values_by_key

    shared = SimpleNamespace(
        selections=[("111", "2025", 1, 1, "Player 1", "RB")],
        stat_seasons=[2024, 2025, 2026],
    )

    async def fake_load_shared_data(db, redis, *, rounds):
        return shared

    async def fake_get_cached_players(db):
        return {"111": SimpleNamespace()}

    class _FakeLoader:
        async def get_season_stats(self, db, season):
            return [SimpleNamespace(player_id="111")]

    class FakeWarService:
        def __init__(self):
            self.loader = _FakeLoader()

        async def calculate_with_data(self, league, shared):
            return [
                SimpleNamespace(
                    player_id="111",
                    starter_war=3.0,
                    roster_war=3.0,
                )
            ]

    monkeypatch.setattr("app.services.draft.rookie_war._load_shared_data", fake_load_shared_data)
    monkeypatch.setattr("app.services.draft.rookie_war._get_cached_players", fake_get_cached_players)
    monkeypatch.setattr("app.services.draft.rookie_war._war_service", FakeWarService())

    # Create picks for current year (2026), 1-yr future (2027), 2-yr future (2028), 3-yr future (2029)
    picks = [
        SimpleNamespace(season="2026", round=1, og_roster_id=1, slot=1, projected_slot=1),
        SimpleNamespace(season="2027", round=1, og_roster_id=2, slot=1, projected_slot=1),
        SimpleNamespace(season="2028", round=1, og_roster_id=3, slot=1, projected_slot=1),
        SimpleNamespace(season="2029", round=1, og_roster_id=4, slot=1, projected_slot=1),
    ]

    res = asyncio.run(
        get_rookie_pick_war_values_by_key(
            db=None,
            picks=picks,
            league_total_rosters=12,
            league_scoring_settings={"rec": 1.0},
            league_roster_positions=["QB", "RB", "BN"],
            redis=None,
        )
    )

    p2026 = res[("2026", 1, 1)].roster_war
    p2027 = res[("2027", 1, 2)].roster_war
    p2028 = res[("2028", 1, 3)].roster_war
    p2029 = res[("2029", 1, 4)].roster_war

    # Future picks must decrease monotonically with time: 2026 > 2027 > 2028 > 2029
    assert p2026 > p2027 > p2028 > p2029
    # 2027 is discounted by ~15% (multiplier ~0.86)
    assert round(p2026 * 0.86, 1) == round(p2027, 1)


