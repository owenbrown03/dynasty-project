from app.services.advisor.strategy import (
    COMPETE,
    HOARD_PICKS,
    REBUILD,
    WIN_NOW,
    detect_strategy,
)


def _detect(**overrides):
    kwargs = dict(
        my_points_for=100.0,
        all_points_for=[100.0, 80.0, 60.0],
        my_wins=1,
        my_losses=1,
        my_starter_age=26.0,
        league_starter_age=26.0,
        my_pick_count=4,
        league_avg_pick_count=4.0,
    )
    kwargs.update(overrides)
    return detect_strategy(**kwargs)


def test_bottom_feeding_with_picks_rebuilds():
    result = _detect(
        my_points_for=50.0,
        my_wins=0,
        my_losses=3,
        my_pick_count=6,
        league_avg_pick_count=4.0,
    )

    assert result.strategy == REBUILD
    assert "picks" in result.reason.lower()


def test_bottom_feeding_without_picks_still_rebuilds():
    result = _detect(
        my_points_for=50.0,
        my_wins=0,
        my_losses=3,
        my_pick_count=2,
        league_avg_pick_count=4.0,
    )

    assert result.strategy == REBUILD


def test_aging_contender_goes_win_now():
    result = _detect(
        my_points_for=110.0,
        my_starter_age=28.5,
        league_starter_age=26.0,
    )

    assert result.strategy == WIN_NOW


def test_young_contender_does_not_go_win_now():
    result = _detect(
        my_points_for=110.0,
        my_starter_age=24.0,
        league_starter_age=26.5,
    )

    assert result.strategy != WIN_NOW


def test_mid_table_pick_rich_hoards():
    result = _detect(
        my_points_for=85.0,
        my_pick_count=8,
        league_avg_pick_count=4.0,
    )

    assert result.strategy == HOARD_PICKS


def test_balanced_roster_competes():
    result = _detect(
        my_points_for=90.0,
        my_starter_age=26.0,
        league_starter_age=26.0,
        my_pick_count=4,
        league_avg_pick_count=4.0,
    )

    assert result.strategy == COMPETE
