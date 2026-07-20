import asyncio
from types import SimpleNamespace

from app.analytics.war.redraft.service import (
    WARService,
    WARSharedData,
)


class CountingNormalizer:
    def __init__(self):
        self.calls = 0

    def normalize(self, **_kwargs):
        self.calls += 1
        return ["normalized-player"]


class CountingEnvironmentCalculator:
    def __init__(self):
        self.calls = 0

    def calculate(self, **_kwargs):
        self.calls += 1
        return {"environment": "value"}


class CountingMerger:
    def __init__(self):
        self.calls = 0

    def merge(self, **_kwargs):
        self.calls += 1
        return [f"merged-{self.calls}"]


def test_calculate_with_data_reuses_in_memory_calculation_cache():
    service = WARService()
    service.normalizer = CountingNormalizer()
    service.environment_calculator = (
        CountingEnvironmentCalculator()
    )
    service.replacement_calculator = SimpleNamespace(
        calculate=lambda **_kwargs: {"starter": 1.0},
    )
    service.replacement_roster_builder = SimpleNamespace(
        build=lambda **_kwargs: ["replacement-player"],
    )
    service.bench_replacement_calculator = SimpleNamespace(
        calculate=lambda **_kwargs: {"bench": 1.0},
    )
    service.war_calculator = SimpleNamespace(
        calculate=lambda **_kwargs: ["war-result"],
    )
    service.merger = CountingMerger()

    league = SimpleNamespace(
        season="2026",
        scoring_settings={"rec": 1.0},
        roster_positions=["QB", "RB", "WR", "TE", "FLEX", "BN"],
        total_rosters=12,
    )
    shared = WARSharedData(
        players={},
        projections=[],
    )

    first = asyncio.run(
        service.calculate_with_data(
            league,
            shared,
        )
    )
    second = asyncio.run(
        service.calculate_with_data(
            league,
            shared,
        )
    )

    assert first == ["merged-1"]
    assert second == first
    assert service.normalizer.calls == 1
    assert service.environment_calculator.calls == 1
    assert service.merger.calls == 1
