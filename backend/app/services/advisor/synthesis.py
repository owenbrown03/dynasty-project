import json
import logging
from datetime import datetime, timezone

from app.core.config import settings
from app.integrations.gemini.client import GeminiClient
from app.schemas.advisor import (
    AdvisorDossier,
    AdvisorPreferenceSummary,
    AdvisorRecommendation,
    AdvisorSynthesisResponse,
)
from app.services.advisor import quota
from app.services.advisor.prompts import (
    SYSTEM_PROMPT,
    render_data_block,
)

logger = logging.getLogger(__name__)

RESPONSE_FORMAT_INSTRUCTION = """\
Respond with ONLY a JSON object (no markdown fences) shaped exactly like:

{
  "summary": "2-3 sentence overview of the manager's trade landscape",
  "recommendations": [
    {
      "headline": "short title for the recommendation",
      "pitch": "one-line message the manager could send to the counterparty",
      "reasoning": "why this trade makes sense using ONLY the provided numbers",
      "confidence": "high|medium|low",
      "proposal_index": <index into the proposals array, or null>
    }
  ],
  "roster_advice": [
    {
      "headline": "short title",
      "pitch": "one-line actionable takeaway",
      "reasoning": "roster construction reasoning using ONLY provided numbers",
      "confidence": "high|medium|low",
      "proposal_index": null
    }
  ]
}

Rank recommendations best-first. Only reference players, managers, and \
numbers present in the data blocks. If the data is thin, return fewer \
recommendations rather than inventing content.
"""


async def synthesize_recommendations(
    *,
    gemini: GeminiClient | None,
    redis,
    dossier: AdvisorDossier,
    preferences: AdvisorPreferenceSummary | None = None,
) -> AdvisorSynthesisResponse:
    if gemini is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=503,
            detail=(
                "AI advisor is not configured "
                "(missing GEMINI_API_KEY)."
            ),
        )

    prompt = _build_prompt(dossier, preferences)

    cached = await _cache_get(redis, prompt)
    model = gemini.config.model

    if cached is not None:
        return _parse_response(
            cached,
            dossier=dossier,
            generated_at=None,
            model=model,
            cached=True,
        )

    await quota.consume_quota(
        redis,
        user_id=None,
    )

    try:
        text = await gemini.read.generate_text(
            prompt,
            system_instruction=SYSTEM_PROMPT,
            generation_config={
                "responseMimeType": "application/json",
                "temperature": 0.4,
            },
        )
    except Exception:
        await quota.refund_quota(redis)
        raise

    await _cache_set(redis, prompt, text)

    return _parse_response(
        text,
        dossier=dossier,
        generated_at=datetime.now(timezone.utc),
        model=model,
        cached=False,
    )


def _build_prompt(
    dossier: AdvisorDossier,
    preferences: AdvisorPreferenceSummary | None = None,
) -> str:
    blocks = [
        render_data_block(
            "Trade proposals (deterministic candidates)",
            [p.model_dump() for p in dossier.proposals],
        ),
        render_data_block(
            "Manager roster contexts per league",
            [r.model_dump() for r in dossier.roster_contexts],
        ),
        render_data_block(
            "Cross-league behavioral signals from leaguemate trades",
            dossier.signals.model_dump(),
        ),
    ]

    if preferences is not None and (
        preferences.likes
        or preferences.dislikes
        or preferences.tags
    ):
        blocks.append(
            render_data_block(
                "Manager preference memory (feedback on past "
                "recommendations — respect these when ranking)",
                preferences.model_dump(),
            )
        )

    return (
        "You are advising a fantasy manager with Sleeper username "
        f"'{dossier.username}'.\n\n"
        + "\n".join(blocks)
        + "\n"
        + RESPONSE_FORMAT_INSTRUCTION
    )


def _parse_response(
    raw_text: str,
    *,
    dossier: AdvisorDossier,
    generated_at,
    model: str,
    cached: bool,
) -> AdvisorSynthesisResponse:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        logger.warning("Advisor synthesis returned invalid JSON")
        payload = {}

    recommendations = []
    for item in payload.get("recommendations") or []:
        index = item.get("proposal_index")

        proposal = None
        if isinstance(index, int) and 0 <= index < len(dossier.proposals):
            proposal = dossier.proposals[index]

        recommendations.append(
            AdvisorRecommendation(
                headline=item.get("headline", ""),
                pitch=item.get("pitch", ""),
                reasoning=item.get("reasoning", ""),
                confidence=item.get("confidence", "medium"),
                proposal=proposal,
            )
        )

    roster_advice = []
    for item in payload.get("roster_advice") or []:
        roster_advice.append(
            AdvisorRecommendation(
                headline=item.get("headline", ""),
                pitch=item.get("pitch", ""),
                reasoning=item.get("reasoning", ""),
                confidence=item.get("confidence", "medium"),
                proposal=None,
            )
        )

    timestamp = (
        generated_at.isoformat()
        if generated_at
        else datetime.now(timezone.utc).isoformat()
    )

    return AdvisorSynthesisResponse(
        summary=payload.get("summary", ""),
        recommendations=recommendations,
        roster_advice=roster_advice,
        generated_at=timestamp,
        model=model or settings.GEMINI_MODEL,
        cached=cached,
    )


async def _cache_get(redis, prompt: str) -> str | None:
    if redis is None:
        return None

    return await quota.get_cached_generation(
        redis,
        model=settings.GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT,
        prompt=prompt,
    )


async def _cache_set(redis, prompt: str, text: str) -> None:
    if redis is None:
        return

    await quota.cache_generation(
        redis,
        model=settings.GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT,
        prompt=prompt,
        payload=text,
    )
