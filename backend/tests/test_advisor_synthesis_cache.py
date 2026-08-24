import asyncio
import json

from app.schemas.advisor import (
    AdvisorDossier,
    AdvisorProposal,
    AdvisorSignalSummary,
)
from app.services.advisor import synthesis


class FakeRedis:
    def __init__(self):
        self.store: dict = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ttl_seconds=None):
        self.store[key] = value

    async def incr_with_ttl(self, key, ttl_seconds=None):
        return 1


class FakeRead:
    def __init__(self, text: str):
        self.text = text
        self.calls = 0

    async def generate_text(self, *args, **kwargs):
        self.calls += 1
        return self.text


class FakeGemini:
    def __init__(self, text: str):
        from types import SimpleNamespace

        self.config = SimpleNamespace(model="gemini-test")
        self.read = FakeRead(text)


def _dossier(market_send_total: float = 100.0) -> AdvisorDossier:
    return AdvisorDossier(
        username="testuser",
        proposals=[
            AdvisorProposal(
                league_id="1",
                league_name="Test League",
                counterparty_id="2",
                counterparty_name="Rival",
                send=[],
                receive=[],
                market_send_total=market_send_total,
                market_receive_total=90.0,
                personal_send_total=1.0,
                personal_receive_total=2.0,
            )
        ],
        roster_contexts=[],
        signals=AdvisorSignalSummary(),
    )


def _llm_payload() -> str:
    return json.dumps(
        {
            "summary": "Summary",
            "recommendations": [],
            "roster_advice": [],
        }
    )


def test_cache_round_trip_preserves_generated_at():
    redis = FakeRedis()
    gemini = FakeGemini(_llm_payload())
    dossier = _dossier()

    first = asyncio.run(
        synthesis.synthesize_recommendations(
            gemini=gemini,
            redis=redis,
            dossier=dossier,
        )
    )

    assert first.cached is False
    assert gemini.read.calls == 1

    stored = next(iter(redis.store.values()))
    envelope = json.loads(stored)
    assert envelope["text"] == _llm_payload()
    assert isinstance(envelope["generated_at"], str)

    second = asyncio.run(
        synthesis.synthesize_recommendations(
            gemini=gemini,
            redis=redis,
            dossier=dossier,
        )
    )

    assert second.cached is True
    assert gemini.read.calls == 1
    assert second.generated_at == envelope["generated_at"]


def test_peek_returns_cached_with_timestamp():
    redis = FakeRedis()
    gemini = FakeGemini(_llm_payload())
    dossier = _dossier()

    asyncio.run(
        synthesis.synthesize_recommendations(
            gemini=gemini,
            redis=redis,
            dossier=dossier,
        )
    )

    peeked = asyncio.run(
        synthesis.peek_cached_recommendations(
            gemini=gemini,
            redis=redis,
            dossier=dossier,
        )
    )

    assert peeked is not None
    assert peeked.cached is True
    assert peeked.generated_at is not None


def test_peek_miss_returns_none():
    redis = FakeRedis()
    gemini = FakeGemini(_llm_payload())

    peeked = asyncio.run(
        synthesis.peek_cached_recommendations(
            gemini=gemini,
            redis=redis,
            dossier=_dossier(),
        )
    )

    assert peeked is None


def test_cache_hit_survives_dossier_value_drift():
    redis = FakeRedis()
    gemini = FakeGemini(_llm_payload())

    asyncio.run(
        synthesis.synthesize_recommendations(
            gemini=gemini,
            redis=redis,
            dossier=_dossier(market_send_total=100.0),
        )
    )

    drifted = asyncio.run(
        synthesis.synthesize_recommendations(
            gemini=gemini,
            redis=redis,
            dossier=_dossier(market_send_total=99999.0),
        )
    )

    assert drifted.cached is True
    assert gemini.read.calls == 1


def test_different_league_scopes_do_not_share_cache():
    redis = FakeRedis()
    gemini = FakeGemini(_llm_payload())

    scoped = _dossier().model_copy(
        update={"scope_league_id": "league-a"}
    )

    asyncio.run(
        synthesis.synthesize_recommendations(
            gemini=gemini,
            redis=redis,
            dossier=scoped,
        )
    )

    other = _dossier().model_copy(
        update={"scope_league_id": "league-b"}
    )
    fresh = asyncio.run(
        synthesis.synthesize_recommendations(
            gemini=gemini,
            redis=redis,
            dossier=other,
        )
    )

    assert fresh.cached is False
    assert gemini.read.calls == 2


def _named_proposal(
    receive_names: list[str],
    send_names: list[str],
) -> AdvisorProposal:
    from app.schemas.advisor import AdvisorPlayerRef

    return AdvisorProposal(
        league_id="1",
        league_name="Test League",
        counterparty_id="2",
        counterparty_name="Rival",
        send=[
            AdvisorPlayerRef(player_id=f"s{i}", name=n)
            for i, n in enumerate(send_names)
        ],
        receive=[
            AdvisorPlayerRef(player_id=f"r{i}", name=n)
            for i, n in enumerate(receive_names)
        ],
    )


def _narrative_dossier(proposals: list[AdvisorProposal]) -> AdvisorDossier:
    return AdvisorDossier(
        username="testuser",
        proposals=proposals,
        roster_contexts=[],
        signals=AdvisorSignalSummary(),
    )


def _llm_payload_for(index: int, name: str, other: str) -> str:
    return json.dumps(
        {
            "summary": "Summary",
            "recommendations": [
                {
                    "headline": f"Acquire {name}",
                    "reasoning": (
                        f"Send {other} to land {name} for the stretch run."
                    ),
                    "confidence": "high",
                    "proposal_index": index,
                },
            ],
            "roster_advice": [],
        }
    )


def test_cached_response_is_byte_stable_across_dossier_changes():
    redis = FakeRedis()
    dossier_a = _narrative_dossier(
        [
            _named_proposal(["Drake Maye"], ["De'Von Achane"]),
            _named_proposal(["Travis Hunter"], ["Tua Tagovailoa"]),
        ]
    )
    gemini = FakeGemini(_llm_payload_for(0, "Drake Maye", "Achane"))

    first = asyncio.run(
        synthesis.synthesize_recommendations(
            gemini=gemini,
            redis=redis,
            dossier=dossier_a,
        )
    )
    assert first.cached is False
    assert first.recommendations[0].proposal is dossier_a.proposals[0]

    # Dossier B: proposals reordered AND content changed (shuffle /
    # trade-block drift). The served card must still carry A's trade.
    dossier_b = _narrative_dossier(
        [
            _named_proposal(["Brock Bowers"], ["Somebody Else"]),
            _named_proposal(["Drake Maye"], ["De'Von Achane"]),
        ]
    )

    second = asyncio.run(
        synthesis.synthesize_recommendations(
            gemini=gemini,
            redis=redis,
            dossier=dossier_b,
        )
    )

    assert second.cached is True
    assert gemini.read.calls == 1
    assert (
        second.recommendations[0].proposal
        == first.recommendations[0].proposal
    )

    peeked = asyncio.run(
        synthesis.peek_cached_recommendations(
            gemini=gemini,
            redis=redis,
            dossier=dossier_b,
        )
    )
    assert peeked is not None
    assert (
        peeked.recommendations[0].proposal
        == first.recommendations[0].proposal
    )


def test_legacy_cache_reparse_drops_mismatched_narrative():
    redis = FakeRedis()

    # Simulate a legacy envelope (raw text only, no stored response)
    # whose narrative references proposal 0 of generation-time
    # dossier A while today's dossier has unrelated content there.
    legacy_text = json.dumps(
        {
            "summary": "Summary",
            "recommendations": [
                {
                    "headline": "Acquire Drake Maye",
                    "reasoning": (
                        "Send Achane to land Drake Maye."
                    ),
                    "confidence": "high",
                    "proposal_index": 0,
                },
            ],
            "roster_advice": [],
        }
    )
    identity = synthesis._cache_identity(_narrative_dossier([]), None)
    from app.services.advisor.quota import build_cache_key

    redis.store[
        build_cache_key(
            model=synthesis.settings.GEMINI_MODEL,
            system_instruction=synthesis.SYSTEM_PROMPT,
            prompt=identity,
        )
    ] = json.dumps(
        {"text": legacy_text, "generated_at": "2026-01-01T00:00:00+00:00"},
    )

    drifted = _narrative_dossier(
        [_named_proposal(["Travis Hunter"], ["Tua Tagovailoa"])],
    )

    parsed = asyncio.run(
        synthesis.peek_cached_recommendations(
            gemini=FakeGemini(legacy_text),
            redis=redis,
            dossier=drifted,
        )
    )

    assert parsed is not None
    assert parsed.recommendations[0].headline == "Acquire Drake Maye"
    assert parsed.recommendations[0].proposal is None


def test_mismatched_attachment_survives_when_players_match():
    narrative_ok = {
        "headline": "Acquire Travis Hunter",
        "reasoning": "Two-way upside; send Tua as the filler.",
        "confidence": "medium",
        "proposal_index": 0,
    }
    proposal = _named_proposal(["Travis Hunter"], ["Tua Tagovailoa"])

    assert synthesis._narrative_references_proposal(
        narrative_ok["headline"],
        narrative_ok["reasoning"],
        proposal,
    )
