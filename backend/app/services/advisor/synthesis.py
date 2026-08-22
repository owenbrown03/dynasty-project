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
      "reasoning": "why this trade makes sense for both sides, using ONLY the provided numbers: why the counterparty accepts (their KTC gain) and why our manager wins on personal value",
      "confidence": "high|medium|low",
      "proposal_index": <index into the proposals array, or null>
    }
  ],
  "roster_advice": [
    {
      "headline": "short title",
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


def _cache_identity(
    dossier: AdvisorDossier,
    preferences: AdvisorPreferenceSummary | None,
) -> str:
    """Stable cache identity for an advisor scope.

    Keyed by user, league scope, and preference settings — NOT by the
    dossier bytes. Underlying data refreshes (WAR merges, KTC syncs)
    change dossier numbers constantly; those must not invalidate a
    cached recommendation. Users refresh explicitly via Regenerate.
    """
    preferences_part = (
        json.dumps(preferences.model_dump(), sort_keys=True)
        if preferences is not None
        else "none"
    )

    return (
        f"advisor-scope\n"
        f"{settings.GEMINI_MODEL}\n"
        f"{SYSTEM_PROMPT}\n"
        f"{dossier.username}\n"
        f"{dossier.scope_league_id or 'all'}\n"
        f"{preferences_part}"
    )


async def peek_cached_recommendations(
    *,
    gemini: GeminiClient | None,
    redis,
    dossier: AdvisorDossier,
    preferences: AdvisorPreferenceSummary | None = None,
) -> AdvisorSynthesisResponse | None:
    """Returns the cached synthesis for this dossier without generating.

    Never consumes quota or calls Gemini; returns None on cache miss.
    """
    if not (dossier.proposals or dossier.roster_contexts):
        return None

    prompt = _build_prompt(dossier, preferences)
    model = (
        gemini.config.model
        if gemini is not None
        else settings.GEMINI_MODEL
    )
    cache_identity = _cache_identity(dossier, preferences)

    cached = await _cache_get(redis, cache_identity)

    if cached is None:
        return None

    text, generated_at = _cached_envelope(cached)

    return _parse_response(
        text,
        dossier=dossier,
        generated_at=generated_at,
        model=model,
        cached=True,
    )


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
    model = gemini.config.model
    has_dossier_content = bool(
        dossier.proposals or dossier.roster_contexts
    )
    cache_identity = _cache_identity(dossier, preferences)

    if has_dossier_content:
        cached = await _cache_get(redis, cache_identity)

        if cached is not None:
            text, generated_at = _cached_envelope(cached)

            return _parse_response(
                text,
                dossier=dossier,
                generated_at=generated_at,
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

    if has_dossier_content:
        await _cache_set(redis, cache_identity, text)

    return _parse_response(
        text,
        dossier=dossier,
        generated_at=datetime.now(timezone.utc).isoformat(),
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
    raw_text: str | None,
    *,
    dossier: AdvisorDossier,
    generated_at: str | None,
    model: str | None,
    cached: bool,
) -> AdvisorSynthesisResponse:
    try:
        payload = (
            json.loads(raw_text)
            if isinstance(raw_text, str)
            else {}
        )
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
                reasoning=item.get("reasoning", ""),
                confidence=item.get("confidence", "medium"),
                proposal=None,
            )
        )

    timestamp = generated_at or datetime.now(
        timezone.utc
    ).isoformat()

    return AdvisorSynthesisResponse(
        summary=payload.get("summary", ""),
        recommendations=recommendations,
        roster_advice=roster_advice,
        generated_at=timestamp,
        model=model or settings.GEMINI_MODEL,
        cached=cached,
    )


def _cached_envelope(cached) -> tuple[str | None, str | None]:
    """Normalizes cache entries to (text, generated_at iso string).

    Entries written before timestamp tracking stored a bare LLM text
    string; newer entries store {"text", "generated_at"} envelopes.
    """
    if isinstance(cached, dict):
        generated_at = cached.get("generated_at")

        return (
            cached.get("text"),
            generated_at
            if isinstance(generated_at, str)
            else None,
        )

    return cached, None


async def _cache_get(redis, prompt: str):
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
        payload={
            "text": text,
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
        },
    )

