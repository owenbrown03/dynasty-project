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


def _dossier() -> AdvisorDossier:
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
                market_send_total=100.0,
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
