from app.services.advisor.strategy import (
    COMPETE,
    HOARD_PICKS,
    REBUILD,
    WIN_NOW,
    detect_strategy,
    is_season_altering_injury as strategy_is_season_altering,
    strategy_from_manager_note,
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


def test_note_rebuild_declaration_pins_strategy():
    result = strategy_from_manager_note(
        "Selling everything, full rebuild for 2027 picks.",
    )

    assert result is not None
    assert result.strategy == REBUILD
    assert result.source == "manager_note"


def test_note_win_now_declaration_pins_strategy():
    result = strategy_from_manager_note("All in this year, win now.")

    assert result is not None
    assert result.strategy == WIN_NOW
    assert result.source == "manager_note"


def test_note_hoard_picks_declaration_pins_strategy():
    result = strategy_from_manager_note(
        "Just collecting picks for the draft capital war.",
    )

    assert result is not None
    assert result.strategy == HOARD_PICKS
    assert result.source == "manager_note"


def test_note_without_direction_falls_back_to_detection():
    assert strategy_from_manager_note("Great league, active traders.") is None
    assert strategy_from_manager_note(None) is None
    assert strategy_from_manager_note("") is None


def test_earliest_direction_wins_in_mixed_note():
    result = strategy_from_manager_note(
        "Thinking win now but maybe rebuild next year.",
    )

    assert result is not None
    assert result.strategy == WIN_NOW


def test_sell_low_phrase_does_not_trigger_rebuild():
    # "buy low sell high" trading chatter is not a teardown declaration.
    assert strategy_from_manager_note(
        "I like to buy low sell high on injured guys.",
    ) is None


def test_owner_fringe_band_upper_middle():
    # Owner-confirmed band: e.g. ranks 7-10 of 12 -> 12-team strengths.
    strengths_12 = [120, 110, 100, 95, 90, 85, 80, 75, 70, 65, 60, 55]

    rank7 = _detect(
        my_strength=80.0,
        all_strengths=strengths_12,
        my_wins=1,
        my_losses=2,
        my_pick_count=4,
        league_avg_pick_count=4.0,
    )
    rank11 = _detect(
        my_strength=60.0,
        all_strengths=strengths_12,
        my_wins=0,
        my_losses=3,
        my_pick_count=4,
        league_avg_pick_count=4.0,
    )
    rank5 = _detect(
        my_strength=90.0,
        all_strengths=strengths_12,
        my_wins=2,
        my_losses=1,
        my_pick_count=4,
        league_avg_pick_count=4.0,
    )

    assert rank7.fringe is True
    assert rank11.fringe is False and rank11.bottom_two is True
    assert rank5.fringe is False


def test_top_not_fringe():
    top = _detect(
        my_strength=100.0,
        all_strengths=[100.0, 80.0, 60.0],
        my_wins=3,
        my_losses=0,
        my_pick_count=4,
        league_avg_pick_count=4.0,
    )

    assert top.fringe is False


def test_season_altering_injury_mapping():
    assert strategy_is_season_altering("IR")
    assert strategy_is_season_altering("Injured Reserve")
    assert strategy_is_season_altering("O")
    assert strategy_is_season_altering("PUP")

    # Weekly designations must NOT read as season-altering.
    assert not strategy_is_season_altering("Q")
    assert not strategy_is_season_altering("D")
    assert not strategy_is_season_altering("DNR")
    assert not strategy_is_season_altering(None)
    assert not strategy_is_season_altering("")
