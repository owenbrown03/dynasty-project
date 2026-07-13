from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.schemas.personal_values import (
    PersonalProjectionOutcomeItem,
    PersonalProjectionSeasonUpdate,
    PersonalValueUpdateRequest,
)
from app.services.personal_values import (
    _merge_saved_projection_seasons,
    _validate_projection_update,
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


def test_validate_projection_update_rejects_empty_future_outcomes():
    payload = PersonalValueUpdateRequest(
        seasons=[
            PersonalProjectionSeasonUpdate(
                season=2026,
                outcomes=[
                    PersonalProjectionOutcomeItem(
                        position_rank=48,
                        probability=100,
                    ),
                ],
            ),
            PersonalProjectionSeasonUpdate(
                season=2027,
                outcomes=[],
            ),
        ],
    )

    with pytest.raises(HTTPException) as exc:
        _validate_projection_update(
            base_season=2026,
            end_season=2027,
            payload=payload,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "2027 must have at least one projection outcome."
