from __future__ import annotations

from math import ceil, isclose

from fastapi import HTTPException, status

from app.analytics.war.dynasty.factory import build_dynasty_war_service
from app.analytics.war.redraft.constants import FANTASY_GAMES_PER_SEASON
from app.schemas.personal_values import (
    PersonalProjectionSeasonItem,
    PersonalValueUpdateRequest,
)

CORE_DYNASTY_POSITIONS = (
    "QB",
    "RB",
    "WR",
    "TE",
)
DYNASTY_POSITIONS = set(CORE_DYNASTY_POSITIONS)


def build_default_projection_seasons(
    *,
    base_season: int,
    end_season: int,
    default_position_rank: int | None,
) -> list[PersonalProjectionSeasonItem]:
    seasons: list[PersonalProjectionSeasonItem] = []

    for season in range(
        base_season,
        end_season + 1,
    ):
        if default_position_rank is not None:
            outcomes = [
                {
                    "position_rank": default_position_rank,
                    "probability": 100.0,
                }
            ]
        else:
            outcomes = []

        seasons.append(
            PersonalProjectionSeasonItem(
                season=season,
                default_position_rank=default_position_rank,
                outcomes=outcomes,
                is_customized=False,
            )
        )

    return seasons


def get_projection_end_season(
    *,
    base_season: int,
    age: float | None,
    position: str,
) -> int:
    if age is None or position not in DYNASTY_POSITIONS:
        return base_season + 4

    dynasty_service = build_dynasty_war_service()
    expected = dynasty_service.projector.expected_games_service.calculate(
        age=age,
        position=position,
    )
    years_remaining = max(
        ceil(expected.years_remaining),
        1,
    )
    return base_season + years_remaining - 1


def validate_projection_update(
    *,
    base_season: int,
    end_season: int,
    payload: PersonalValueUpdateRequest,
) -> None:
    expected_seasons = {
        season
        for season in range(
            base_season,
            end_season + 1,
        )
    }

    seen: set[int] = set()

    for item in payload.seasons:
        if item.season not in expected_seasons:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{item.season} is not a supported projection season.",
            )

        if item.season in seen:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{item.season} was submitted more than once.",
            )

        seen.add(item.season)

        if not item.outcomes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{item.season} must have at least one projection outcome.",
            )

        if item.season == base_season:
            if len(item.outcomes) != 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{item.season} must have exactly one current-year outcome.",
                )

            if not isclose(
                float(item.outcomes[0].probability),
                100.0,
                abs_tol=0.01,
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{item.season} current-year probability must be 100%.",
                )
        total_probability = sum(
            float(outcome.probability)
            for outcome in item.outcomes
        )

        if not isclose(
            total_probability,
            100.0,
            abs_tol=0.01,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{item.season} probabilities must total 100%.",
            )

        for outcome in item.outcomes:
            if outcome.position_rank <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{item.season} position rank must be greater than zero.",
                )

            if outcome.probability <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{item.season} probability must be greater than zero.",
                )


def project_custom_dynasty_war(
    *,
    age: float | None,
    position: str,
    current_season: int,
    season_values: dict[int, float],
) -> float | None:
    if age is None or position not in DYNASTY_POSITIONS:
        return None

    dynasty_service = build_dynasty_war_service()
    expected = dynasty_service.projector.expected_games_service.calculate(
        age=age,
        position=position,
    )

    total = 0.0

    for season, season_war in sorted(
        season_values.items(),
        key=lambda item: item[0],
    ):
        offset = season - current_season

        if offset < 0:
            continue

        season_fraction = min(
            max(
                expected.years_remaining - offset,
                0.0,
            ),
            1.0,
        )

        if season_fraction <= 0:
            continue

        if offset == 0:
            discount = 1.0
        else:
            midpoint_game = (
                offset * FANTASY_GAMES_PER_SEASON
                + max(
                    (season_fraction * FANTASY_GAMES_PER_SEASON) / 2,
                    1,
                )
            )
            discount = dynasty_service.projector.discount_curve.multiplier(
                midpoint_game,
            )

        total += season_war * season_fraction * discount

    return round(total, 2)


def merge_saved_projection_seasons(
    *,
    base_season: int,
    end_season: int,
    default_position_rank: int | None,
    saved_projections,
    outcomes_by_projection_id: dict[int, list],
) -> list[PersonalProjectionSeasonItem]:
    base_seasons = build_default_projection_seasons(
        base_season=base_season,
        end_season=end_season,
        default_position_rank=default_position_rank,
    )
    saved_payload_by_season: dict[int, tuple[list[dict[str, float]], bool]] = {}

    for projection in saved_projections:
        saved_payload_by_season[
            projection.season
        ] = (
            [
                {
                    "position_rank": outcome.position_rank,
                    "probability": outcome.probability,
                }
                for outcome in outcomes_by_projection_id.get(
                    projection.id,
                    [],
                )
            ],
            projection.is_customized,
        )

    merged_seasons: list[PersonalProjectionSeasonItem] = []

    for season_item in base_seasons:
        saved_outcomes, is_customized = saved_payload_by_season.get(
            season_item.season,
            (
                season_item.outcomes,
                season_item.is_customized,
            ),
        )

        merged_seasons.append(
            PersonalProjectionSeasonItem(
                season=season_item.season,
                default_position_rank=season_item.default_position_rank,
                outcomes=saved_outcomes,
                is_customized=is_customized,
            )
        )

    return merged_seasons
