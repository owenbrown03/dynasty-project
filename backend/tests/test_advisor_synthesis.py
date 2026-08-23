import asyncio
import json

import pytest

from app.schemas.advisor import (
    AdvisorDossier,
    AdvisorPlayerRef,
    AdvisorProposal,
    AdvisorSignalSummary,
)
from app.services.advisor import synthesis


class FakeGemini:
    def __init__(self, text: str):
        from app.integrations.gemini.config import GeminiConfig

        self.config = GeminiConfig(api_key="k", model="test-model")
        self._text = text
        self.calls = 0

        class _Read:
            def __init__(self, outer):
                self.outer = outer

            async def generate_text(self, prompt, **kwargs):
                self.outer.calls += 1
                return self.outer._text

        self.read = _Read(self)


class RedisStub:
    def __init__(self):
        self.store: dict = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ttl_seconds=None):
        self.store[key] = value

    async def incr_with_ttl(self, key, ttl_seconds):
        return 1

    async def delete(self, key):
        self.store.pop(key, None)


def _dossier() -> AdvisorDossier:
    proposal = AdvisorProposal(
        league_id="l1",
        league_name="Test League",
        counterparty_id="u2",
        counterparty_name="Leaguemate",
        send=[
            AdvisorPlayerRef(
                player_id="p1",
                name="Veteran RB",
                position="RB",
                ktc_value=2100,
                personal_war=1.5,
            )
        ],
        receive=[
            AdvisorPlayerRef(
                player_id="p2",
                name="Young WR",
                position="WR",
                ktc_value=2000,
                personal_war=2.6,
            )
        ],
        market_send_total=2100,
        market_receive_total=2000,
        personal_send_total=1.5,
        personal_receive_total=2.6,
    )

    return AdvisorDossier(
        username="owen",
        proposals=[proposal],
        roster_contexts=[],
        signals=AdvisorSignalSummary(
            buy_targets=["Young WR"],
        ),
    )


def _valid_response_text() -> str:
    return json.dumps(
        {
            "summary": "You can win a value gap.",
            "recommendations": [
                {
                    "headline": "Swap vet RB for breakout WR",
                    "pitch": "Would you do Veteran RB for Young WR?",
                    "reasoning": "Personal WAR 2.6 vs 1.5 while KTC is near even.",
                    "confidence": "high",
                    "proposal_index": 0,
                }
            ],
            "roster_advice": [],
        }
    )


def test_synthesis_binds_proposal_and_caches():
    redis = RedisStub()
    gemini = FakeGemini(_valid_response_text())

    result = asyncio.run(
        synthesis.synthesize_recommendations(
            gemini=gemini,
            redis=redis,
            dossier=_dossier(),
        )
    )

    assert gemini.calls == 1
    assert result.cached is False
    assert len(result.recommendations) == 1

    rec = result.recommendations[0]
    assert rec.proposal is not None
    assert rec.proposal.counterparty_name == "Leaguemate"

    second = asyncio.run(
        synthesis.synthesize_recommendations(
            gemini=gemini,
            redis=redis,
            dossier=_dossier(),
        )
    )

    assert gemini.calls == 1
    assert second.cached is True


def test_synthesis_handles_invalid_json():
    gemini = FakeGemini("not json at all")

    result = asyncio.run(
        synthesis.synthesize_recommendations(
            gemini=gemini,
            redis=RedisStub(),
            dossier=_dossier(),
        )
    )

    assert result.summary == ""
    assert result.recommendations == []


def test_synthesis_requires_client():
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            synthesis.synthesize_recommendations(
                gemini=None,
                redis=RedisStub(),
                dossier=_dossier(),
            )
        )

    assert exc.value.status_code == 503


def test_prompt_contains_data_blocks_and_rules():
    prompt = synthesis._build_prompt(_dossier())

    assert "Trade proposals" in prompt
    assert "Veteran RB" in prompt
    assert "buy_targets" in prompt
    assert "ONLY" in synthesis.RESPONSE_FORMAT_INSTRUCTION
