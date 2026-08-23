from app.services.advisor.strategy import (
    COMPETE,
    HOARD_PICKS,
    REBUILD,
    WIN_NOW,
    detect_strategy,
)


from app.services.advisor.strategy import (
    BASIS_ACTUAL_POINTS,
    BASIS_PROJECTED_WAR,
)


def _detect(**overrides):
    kwargs = dict(
        my_strength=100.0,
        all_strengths=[100.0, 80.0, 60.0],
        basis=BASIS_ACTUAL_POINTS,
        my_wins=3,
        my_losses=0,
        my_starter_age=26.0,
        league_starter_age=26.0,
        my_pick_count=4,
        league_avg_pick_count=4.0,
    )
    kwargs.update(overrides)
    return detect_strategy(**kwargs)


def test_bottom_feeding_with_picks_rebuilds():
    result = _detect(
        my_strength=50.0,
        all_strengths=[100.0, 80.0, 50.0],
        my_wins=0,
        my_losses=3,
        my_pick_count=6,
        league_avg_pick_count=4.0,
    )

    assert result.strategy == REBUILD
    assert "picks" in result.reason.lower()


def test_bottom_feeding_without_picks_still_rebuilds():
    result = _detect(
        my_strength=50.0,
        all_strengths=[100.0, 80.0, 50.0],
        my_wins=0,
        my_losses=3,
        my_pick_count=2,
        league_avg_pick_count=4.0,
    )

    assert result.strategy == REBUILD


def test_aging_contender_goes_win_now():
    result = _detect(
        my_strength=110.0,
        my_starter_age=28.5,
        league_starter_age=26.0,
    )

    assert result.strategy == WIN_NOW


def test_young_contender_does_not_go_win_now():
    result = _detect(
        my_strength=110.0,
        my_starter_age=24.0,
        league_starter_age=26.5,
    )

    assert result.strategy != WIN_NOW


def test_mid_table_pick_rich_hoards():
    result = _detect(
        my_strength=85.0,
        all_strengths=[100.0, 90.0, 85.0, 60.0],
        my_wins=1,
        my_losses=2,
        my_pick_count=8,
        league_avg_pick_count=4.0,
    )

    assert result.strategy == HOARD_PICKS


def test_balanced_roster_competes():
    result = _detect(
        my_strength=90.0,
        all_strengths=[100.0, 95.0, 90.0, 80.0],
        my_wins=2,
        my_losses=1,
        my_starter_age=26.0,
        league_starter_age=26.0,
        my_pick_count=4,
        league_avg_pick_count=4.0,
    )

    assert result.strategy == COMPETE


def test_preseason_zero_points_cannot_claim_strength():
    # Everyone at zero points in the preseason: ranking by points
    # would be noise, so the projected-WAR basis decides and the
    # reason says "projected starter WAR", never a points rank.
    result = _detect(
        basis=BASIS_PROJECTED_WAR,
        my_strength=None,
        all_strengths=[None],
        my_wins=0,
        my_losses=0,
    )

    assert "points" not in result.reason.lower()
    assert "projected starter war" in result.reason.lower()


def test_preseason_old_projected_contender_goes_win_now():
    # 0-0 record must not block win-now when projections say the
    # roster is strong and old.
    result = _detect(
        basis=BASIS_PROJECTED_WAR,
        my_strength=120.0,
        all_strengths=[120.0, 70.0, 60.0],
        my_wins=0,
        my_losses=0,
        my_starter_age=28.5,
        league_starter_age=25.5,
    )

    assert result.strategy == WIN_NOW
    assert "projected" in result.reason.lower()
