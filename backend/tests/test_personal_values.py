from types import SimpleNamespace

from app.services.personal_values import (
    _merge_saved_projection_seasons,
)


def test_merge_saved_projection_seasons_returns_new_frozen_items():
    merged = _merge_saved_projection_seasons(
        base_season=2026,
        end_season=2029,
        default_position_rank=48,
        saved_projections=[
            SimpleNamespace(
                id=10,
                season=2027,
                is_customized=True,
            ),
        ],
        outcomes_by_projection_id={
            10: [
                SimpleNamespace(
                    position_rank=42,
                    probability=60.0,
                ),
                SimpleNamespace(
                    position_rank=55,
                    probability=40.0,
                ),
            ],
        },
    )

    current = next(
        season
        for season in merged
        if season.season == 2026
    )
    future = next(
        season
        for season in merged
        if season.season == 2027
    )

    assert len(current.outcomes) == 1
    assert current.outcomes[0].position_rank == 48
    assert current.outcomes[0].probability == 100.0
    assert current.is_customized is False

    assert [
        (outcome.position_rank, outcome.probability)
        for outcome in future.outcomes
    ] == [
        (42, 60.0),
        (55, 40.0),
    ]
    assert future.is_customized is True
