import json
import logging
import re
from types import SimpleNamespace
from datetime import datetime, timezone

from app.core.config import settings
from app.integrations.gemini.client import GeminiClient
from app.schemas.advisor import (
    AdvisorDossier,
    AdvisorPreferenceSummary,
    AdvisorProposal,
    AdvisorRecommendation,
    AdvisorSynthesisResponse,
)
from app.services.advisor import quota
from app.services.advisor.candidates import (
    ADVISOR_ENGINE_VERSION,
)
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
        f"{ADVISOR_ENGINE_VERSION}\n"
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

    stable = _response_from_cache(cached)

    if stable is not None:
        return stable

    # Legacy envelope: raw text written before responses were cached
    # fully parsed. Reparsing against today's dossier can pair old
    # narratives with new trades, so the defensive validator below
    # drops mismatched attachments.
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
    force: bool = False,
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

    if has_dossier_content and not force:
        cached = await _cache_get(redis, cache_identity)

        if cached is not None:
            stable = _response_from_cache(cached)

            if stable is not None:
                return stable

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
                # Explicit regenerations should offer genuinely
                # different takes on the same data, so sample
                # hotter than the initial generation.
                "temperature": 0.95 if force else 0.4,
            },
        )
    except Exception:
        await quota.refund_quota(redis)
        raise

    if has_dossier_content:
        parsed = _parse_response(
            text,
            dossier=dossier,
            generated_at=datetime.now(
                timezone.utc
            ).isoformat(),
            model=model,
            cached=False,
        )
        await _cache_set(redis, cache_identity, text, parsed)

        return parsed

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

            if not _narrative_references_proposal(
                item.get("headline"),
                item.get("reasoning"),
                proposal,
            ):
                logger.warning(
                    "Advisor recommendation narrative does not reference "
                    "its attached proposal (index=%s); dropping the "
                    "attachment to avoid mismatched cards",
                    index,
                )
                proposal = None

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


async def _cache_set(
    redis,
    prompt: str,
    text: str,
    response: AdvisorSynthesisResponse | None = None,
) -> None:
    if redis is None:
        return

    payload = {
        "text": text,
        "generated_at": (
            response.generated_at
            if response is not None
            else datetime.now(timezone.utc).isoformat()
        ),
    }

    if response is not None:
        # Store the fully parsed response (proposals embedded) so
        # later reads serve byte-stable cards even when the dossier
        # was rebuilt with different proposal ordering/content.
        payload["response"] = json.loads(
            response.model_dump_json()
        )

    await quota.cache_generation(
        redis,
        model=settings.GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT,
        prompt=prompt,
        payload=payload,
    )


def _response_from_cache(
    cached,
) -> AdvisorSynthesisResponse | None:
    """Rebuilds a cached fully-parsed response, if present.

    Returns None for legacy entries that only carry raw LLM text.
    """
    if not isinstance(cached, dict):
        return None

    stored = cached.get("response")

    if not isinstance(stored, dict):
        return None

    try:
        response = AdvisorSynthesisResponse.model_validate(stored)
    except Exception:
        logger.warning(
            "Advisor synthesis cache held an invalid stored response; "
            "falling back to reparse",
        )
        return None

    return response.model_copy(update={"cached": True})


def _narrative_references_proposal(
    headline: str | None,
    reasoning: str | None,
    proposal: AdvisorProposal,
) -> bool:
    """Guards narrative<->proposal pairing.

    A card claiming a trade must reference at least one player
    actually in the proposal (either direction). Pick-only swaps are
    exempt. Tokens are matched on word boundaries so partial-name
    phrasing ("Achane" for "De'Von Achane", "vet RB" for
    "Veteran RB") still counts.
    """
    tokens: list[str] = []

    for ref in [*proposal.send, *proposal.receive]:
        name = (ref.name or "").strip()
        if not name:
            continue

        casefolded = name.casefold()
        tokens.append(casefolded)

        for word in casefolded.split():
            if len(word) >= 2 and word not in tokens:
                tokens.append(word)

    if not tokens:
        return True

    text = f"{headline or ''} {reasoning or ''}".casefold()

    return any(
        re.search(rf"\b{re.escape(token)}\b", text)
        for token in tokens
    )


async def invalidate_cached_recommendations(
    *,
    redis,
    username: str,
    league_id: str | None,
    preferences: AdvisorPreferenceSummary | None = None,
) -> bool:
    """Drops the cached synthesis for this scope.

    The cache identity only depends on scope fields, so a full
    dossier build is unnecessary here.
    """
    if redis is None:
        return False

    identity = _cache_identity(
        SimpleNamespace(
            username=username,
            scope_league_id=league_id,
        ),
        preferences,
    )

    from app.services.advisor.quota import build_cache_key

    key = build_cache_key(
        model=settings.GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT,
        prompt=identity,
    )

    await redis.delete(key)
    return True
