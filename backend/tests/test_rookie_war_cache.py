import asyncio
import json
from types import SimpleNamespace

from app.services.draft.rookie_war import (
    RookiePickWarAggregate,
    _deserialize_aggregates,
    _load_shared_data,
    _sel_attr,
    _serialize_aggregates,
    build_rookie_war_config_fingerprint,
    get_rookie_pick_war_values_by_key,
)


def _assert_all_fields(selection, expected_player_id="12345"):
    assert _sel_attr(selection, "player_id") == expected_player_id
    assert _sel_attr(selection, "season") == "2025"
    assert _sel_attr(selection, "round") == 2
    assert _sel_attr(selection, "round_slot") == 7


def test_sel_attr_handles_db_tuples():
    _assert_all_fields(("12345", "2025", 2, 7))


def test_sel_attr_handles_json_deserialized_lists():
    _assert_all_fields(["12345", "2025", 2, 7])


def test_sel_attr_handles_dicts():
    _assert_all_fields(
        {
            "player_id": "12345",
            "season": "2025",
            "round": 2,
            "round_slot": 7,
        }
    )


def test_sel_attr_returns_none_for_unknown_field():
    selection = ["12345", "2025", 2, 7]
    assert _sel_attr(selection, "unknown") is None


def test_load_shared_data_normalizes_cached_selections(monkeypatch):
    cached_payload = {
        "selections": [["12345", "2025", 2, 7], ["67890", "2024", 1, 3]],
        "stat_seasons": [2024, 2025],
    }

    class FakeRedis:
        async def get(self, key):
            return json.dumps(cached_payload)

    def _fail(*_args, **_kwargs):
        raise AssertionError("DB must not be hit when redis cache hits")

    monkeypatch.setattr(
        "app.services.draft.rookie_war.get_historical_rookie_draft_selections",
        _fail,
    )
    monkeypatch.setattr(
        "app.services.draft.rookie_war.get_available_stat_seasons",
        _fail,
    )

    shared = asyncio.run(
        _load_shared_data(
            db=None,
            redis=FakeRedis(),
            rounds=[1, 2],
        )
    )

    assert shared.stat_seasons == [2024, 2025]
    for selection in shared.selections:
        assert isinstance(selection, tuple)
        assert _sel_attr(selection, "player_id") is not None


def test_aggregate_serialization_round_trip():
    resolved = {
        ("2027", 1, 5): RookiePickWarAggregate(
            starter_war=0.12,
            roster_war=0.34,
            sample_size=42,
            source_label="Historical rookie WAR from 42 past 1.05 outcomes",
        ),
        ("2027", 2, 9): RookiePickWarAggregate(
            starter_war=-0.01,
            roster_war=0.08,
            sample_size=17,
            source_label="round 2",
        ),
    }

    restored = _deserialize_aggregates(
        json.loads(json.dumps(_serialize_aggregates(resolved)))
    )

    assert restored == resolved


def test_fingerprint_changes_when_stat_seasons_advance():
    base_kwargs = dict(
        league_total_rosters=12,
        league_scoring_settings={"rec": 1.0},
        league_roster_positions=["QB", "RB", "BN"],
        rounds=[1],
        seasons=["2027"],
        effective_slots=[1],
    )

    before = build_rookie_war_config_fingerprint(
        latest_completed_season=2025,
        **base_kwargs,
    )
    after = build_rookie_war_config_fingerprint(
        latest_completed_season=2026,
        **base_kwargs,
    )

    assert before != after


def test_fingerprint_changes_when_league_shape_changes():
    base_kwargs = dict(
        league_total_rosters=12,
        rounds=[1],
        seasons=["2027"],
        effective_slots=[1],
        latest_completed_season=2025,
    )

    ppr = build_rookie_war_config_fingerprint(
        league_scoring_settings={"rec": 1.0},
        league_roster_positions=["QB", "RB", "BN"],
        **base_kwargs,
    )
    half = build_rookie_war_config_fingerprint(
        league_scoring_settings={"rec": 0.5},
        league_roster_positions=["QB", "RB", "BN"],
        **base_kwargs,
    )
    superflex = build_rookie_war_config_fingerprint(
        league_scoring_settings={"rec": 1.0},
        league_roster_positions=["QB", "QB", "RB", "BN"],
        **base_kwargs,
    )

    assert len({ppr, half, superflex}) == 3


class _InMemoryRedis:
    def __init__(self):
        self.store = {}
        self.set_calls = 0

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ttl_seconds=None):
        self.store[key] = value
        self.set_calls += 1


def test_aggregate_cache_hit_skips_recomputation(monkeypatch):
    shared = SimpleNamespace(
        selections=[tuple(["111", "2025", 1, 1])],
        stat_seasons=[2024, 2025],
    )
    calc_calls = {"count": 0}

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
            calc_calls["count"] += 1
            return [
                SimpleNamespace(
                    player_id="111",
                    starter_war=1.0,
                    roster_war=2.0,
                )
            ]

    monkeypatch.setattr(
        "app.services.draft.rookie_war._load_shared_data",
        fake_load_shared_data,
    )
    monkeypatch.setattr(
        "app.services.draft.rookie_war._get_cached_players",
        fake_get_cached_players,
    )
    monkeypatch.setattr(
        "app.services.draft.rookie_war._war_service",
        FakeWarService(),
    )

    picks = [
        SimpleNamespace(
            season="2027",
            round=1,
            og_roster_id=5,
            slot=None,
            projected_slot=None,
        )
    ]
    redis = _InMemoryRedis()
    kwargs = dict(
        picks=picks,
        league_total_rosters=12,
        league_scoring_settings={"rec": 1.0},
        league_roster_positions=["QB", "RB", "BN"],
        redis=redis,
    )

    first = asyncio.run(get_rookie_pick_war_values_by_key(db=None, **kwargs))
    assert first[("2027", 1, 5)].roster_war == 2.0
    assert calc_calls["count"] == 2

    second = asyncio.run(get_rookie_pick_war_values_by_key(db=None, **kwargs))
    assert second == first
    assert calc_calls["count"] == 2
    assert redis.set_calls == 1


def test_empty_result_is_not_cached(monkeypatch):
    async def fake_load_shared_data(db, redis, *, rounds):
        return SimpleNamespace(selections=[], stat_seasons=[])

    monkeypatch.setattr(
        "app.services.draft.rookie_war._load_shared_data",
        fake_load_shared_data,
    )

    redis = _InMemoryRedis()
    result = asyncio.run(
        get_rookie_pick_war_values_by_key(
            db=None,
            picks=[
                SimpleNamespace(
                    season="2027",
                    round=1,
                    og_roster_id=5,
                    slot=None,
                    projected_slot=None,
                )
            ],
            league_total_rosters=12,
            league_scoring_settings={"rec": 1.0},
            league_roster_positions=["QB", "RB", "BN"],
            redis=redis,
        )
    )

    assert result == {}
    assert redis.store == {}
