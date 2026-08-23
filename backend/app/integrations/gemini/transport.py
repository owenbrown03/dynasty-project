import asyncio
import logging

import httpx

from .config import GeminiConfig
from .schemas import GeminiGenerateResponse, GeminiUsageMetadata

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503}
_MAX_SERVER_RETRY_DELAY_SECONDS = 10.0


def _server_retry_delay_seconds(
    exc: httpx.HTTPStatusError,
) -> float | None:
    """
    Extracts a server-provided wait hint from a failed Gemini response.

    Prefers the Retry-After header, then falls back to a google.rpc.RetryInfo
    detail entry carrying retryDelay (e.g. "26s") as returned for 429s.
    """
    retry_after = exc.response.headers.get("Retry-After")

    if retry_after:
        try:
            return min(float(retry_after), _MAX_SERVER_RETRY_DELAY_SECONDS)
        except ValueError:
            pass

    try:
        payload = exc.response.json()
    except Exception:
        return None

    error_payload = payload.get("error")

    if not isinstance(error_payload, dict):
        return None

    for detail in error_payload.get("details") or []:
        if not isinstance(detail, dict):
            continue

        if not str(detail.get("@type", "")).endswith("RetryInfo"):
            continue

        raw = str(detail.get("retryDelay", "")).removesuffix("s")

        try:
            return min(float(raw), _MAX_SERVER_RETRY_DELAY_SECONDS)
        except ValueError:
            continue

    return None


def _daily_quota_exhausted(exc: httpx.HTTPStatusError) -> bool:
    """
    Detects a per-day quota exhaustion in a 429 response.

    Google marks these with a google.rpc.QuotaFailure detail whose
    violations carry a quotaId containing "PerDay" (e.g.
    GenerateRequestsPerDayPerProjectPerModel-FreeTier). Waiting seconds
    does not help with those; only switching models or the daily reset does.
    """
    try:
        payload = exc.response.json()
    except Exception:
        return False

    error_payload = payload.get("error")

    if not isinstance(error_payload, dict):
        return False

    for detail in error_payload.get("details") or []:
        if not isinstance(detail, dict):
            continue

        if not str(detail.get("@type", "")).endswith("QuotaFailure"):
            continue

        for violation in detail.get("violations") or []:
            if not isinstance(violation, dict):
                continue

            if "PerDay" in str(violation.get("quotaId", "")):
                return True

    return False


class GeminiTransport:
    def __init__(
        self,
        *,
        http: httpx.AsyncClient,
        config: GeminiConfig,
    ):
        self.http = http
        self.config = config

    def _url(self, model: str, method: str) -> str:
        return (
            f"{self.config.base_url}"
            f"/models/{model}:{method}"
        )

    async def generate_content(
        self,
        *,
        contents: list[dict],
        system_instruction: str | None = None,
        generation_config: dict | None = None,
    ) -> GeminiGenerateResponse:
        """Generates content, walking the configured model fallback chain.

        Each model gets the full attempt budget. The chain advances when a
        model is unavailable (404) or its daily quota is exhausted (429 with
        a PerDay QuotaFailure); all other failures retry the same model and
        eventually propagate.
        """
        if not self.config.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured"
            )

        body: dict = {"contents": contents}

        if system_instruction:
            body["systemInstruction"] = {
                "parts": [{"text": system_instruction}],
            }

        if generation_config:
            body["generationConfig"] = generation_config

        last_error: httpx.HTTPStatusError | None = None

        for model in self.config.model_chain:
            for attempt in range(max(1, self.config.max_attempts)):
                try:
                    response = await self.http.post(
                        self._url(model, "generateContent"),
                        headers={
                            "x-goog-api-key": self.config.api_key,
                        },
                        json=body,
                        timeout=self.config.timeout_seconds,
                    )
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    last_error = exc
                    status = exc.response.status_code

                    if status == 404:
                        logger.warning(
                            "Gemini model %s unavailable; trying next fallback",
                            model,
                        )
                        break

                    if status == 429 and _daily_quota_exhausted(exc):
                        logger.warning(
                            "Gemini model %s daily quota exhausted; "
                            "switching to next fallback",
                            model,
                        )
                        break

                    is_last_attempt = attempt == self.config.max_attempts - 1
                    if (
                        status not in _RETRYABLE_STATUS_CODES
                        or is_last_attempt
                    ):
                        raise

                    logger.warning(
                        "Gemini generate attempt %d/%d on %s failed status=%d",
                        attempt + 1,
                        self.config.max_attempts,
                        model,
                        status,
                    )
                    wait = self.config.retry_backoff_seconds * (attempt + 1)
                    server_delay = _server_retry_delay_seconds(exc)

                    if server_delay is not None and server_delay > wait:
                        logger.info(
                            "Gemini requested retry delay of %.1fs",
                            server_delay,
                        )
                        wait = server_delay

                    await asyncio.sleep(wait)
                except (httpx.TimeoutException, httpx.TransportError) as exc:
                    # Timeouts are costly (a full timeout window each), so
                    # unlike retryable statuses they advance straight to the
                    # next model instead of burning the attempt budget.
                    last_error = exc
                    logger.warning(
                        "Gemini model %s failed with %s; trying next fallback",
                        model,
                        type(exc).__name__,
                    )
                    break
                else:
                    return _parse_generate_response(
                        response.json(),
                    )

        raise last_error  # pragma: no cover - loop always returns or raises


def _parse_generate_response(payload: dict) -> GeminiGenerateResponse:
    candidates = payload.get("candidates") or []
    text = ""
    finish_reason = None

    if candidates:
        candidate = candidates[0]
        finish_reason = candidate.get("finishReason")
        parts = candidate.get("content", {}).get("parts") or []
        text = "".join(
            part.get("text", "")
            for part in parts
            if "text" in part
        )

    usage_payload = payload.get("usageMetadata") or {}

    return GeminiGenerateResponse(
        text=text,
        model_version=payload.get("modelVersion"),
        usage=GeminiUsageMetadata(**usage_payload),
    )
