from __future__ import annotations

from app.schemas.finance import FinancePlacePayout

PLAYOFF_FINISH_PROBABILITY_BY_SEED = {
    1: {
        1: 0.3191,
        2: 0.2480,
        3: 0.2289,
        4: 0.2041,
        5: 0.0,
        6: 0.0,
    },
    2: {
        1: 0.2638,
        2: 0.2807,
        3: 0.2277,
        4: 0.2277,
        5: 0.0,
        6: 0.0,
    },
    3: {
        1: 0.1443,
        2: 0.1375,
        3: 0.1635,
        4: 0.1522,
        5: 0.2503,
        6: 0.1522,
    },
    4: {
        1: 0.1105,
        2: 0.1184,
        3: 0.1691,
        4: 0.1409,
        5: 0.2469,
        6: 0.2142,
    },
    5: {
        1: 0.0823,
        2: 0.1218,
        3: 0.1105,
        4: 0.1443,
        5: 0.2627,
        6: 0.2740,
    },
    6: {
        1: 0.0789,
        2: 0.0891,
        3: 0.0981,
        4: 0.1184,
        5: 0.2322,
        6: 0.3529,
    },
}


def calculate_projected_winnings(
    *,
    buy_in_amount: float,
    total_rosters: int,
    playoff_teams: int,
    rank: int | None,
) -> float:
    if (
        buy_in_amount <= 0
        or total_rosters <= 0
        or playoff_teams <= 0
        or rank is None
        or rank > playoff_teams
    ):
        return 0.0

    prize_pool = buy_in_amount * total_rosters
    weights = list(
        range(
            playoff_teams,
            0,
            -1,
        )
    )
    weight_total = sum(weights)
    weight = weights[rank - 1]

    return round(
        prize_pool * weight / weight_total,
        2,
    )


def build_seed_finish_probabilities(
    *,
    seed: int | None,
    total_rosters: int,
    playoff_teams: int,
) -> dict[int, float]:
    if seed is None or seed <= 0:
        return {}

    return dict(
        PLAYOFF_FINISH_PROBABILITY_BY_SEED.get(
            seed,
            {},
        )
    )


def normalize_payout_structure(
    payout_structure: dict[str, float] | None,
) -> dict[str, float]:
    if not payout_structure:
        return {}

    normalized: dict[str, float] = {}

    for key, value in payout_structure.items():
        if value <= 0:
            continue

        try:
            place = int(key)
        except (
            TypeError,
            ValueError,
        ):
            continue

        if place <= 0:
            continue

        normalized[str(place)] = round(
            float(value),
            2,
        )

    return normalized


def calculate_expected_winnings_from_seed(
    *,
    payout_structure: dict[str, float] | None,
    projected_seed: int | None,
    total_rosters: int,
    playoff_teams: int,
) -> float | None:
    normalized_payouts = normalize_payout_structure(
        payout_structure,
    )

    if not normalized_payouts:
        return None

    if (
        projected_seed is None
        or projected_seed not in PLAYOFF_FINISH_PROBABILITY_BY_SEED
    ):
        return 0.0

    probabilities = build_seed_finish_probabilities(
        seed=projected_seed,
        total_rosters=total_rosters,
        playoff_teams=playoff_teams,
    )

    if not probabilities:
        return None

    expected = 0.0

    for place_key, payout in normalized_payouts.items():
        expected += payout * probabilities.get(
            int(place_key),
            0.0,
        )

    return round(
        expected,
        2,
    )


def serialize_payout_structure(
    payout_structure: dict[str, float] | None,
) -> list[FinancePlacePayout]:
    normalized = normalize_payout_structure(
        payout_structure,
    )
    return [
        FinancePlacePayout(
            place=int(place),
            amount=amount,
        )
        for place, amount in sorted(
            normalized.items(),
            key=lambda item: int(item[0]),
        )
    ]


def payout_for_rank(
    payout_structure: dict[str, float] | None,
    rank: int | None,
) -> float | None:
    if rank is None:
        return None

    normalized = normalize_payout_structure(
        payout_structure,
    )

    if str(rank) not in normalized:
        return None

    return normalized[str(rank)]
