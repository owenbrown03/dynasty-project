import httpx

from .config import GeminiConfig
from .schemas import GeminiGenerateResponse, GeminiUsageMetadata


class GeminiTransport:
    def __init__(
        self,
        *,
        http: httpx.AsyncClient,
        config: GeminiConfig,
    ):
        self.http = http
        self.config = config

    def _url(self, method: str) -> str:
        return (
            f"{self.config.base_url}"
            f"/models/{self.config.model}:{method}"
        )

    async def generate_content(
        self,
        *,
        contents: list[dict],
        system_instruction: str | None = None,
        generation_config: dict | None = None,
    ) -> GeminiGenerateResponse:
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

        response = await self.http.post(
            self._url("generateContent"),
            params={"key": self.config.api_key},
            json=body,
            timeout=self.config.timeout_seconds,
        )

        response.raise_for_status()

        return _parse_generate_response(
            response.json(),
        )


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
