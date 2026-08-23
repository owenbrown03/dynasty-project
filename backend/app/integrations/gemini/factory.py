from app.core.config import settings

from .client import GeminiClient
from .config import GeminiConfig


def build_gemini_config() -> GeminiConfig:
    return GeminiConfig(
        api_key=settings.GEMINI_API_KEY,
        model=settings.GEMINI_MODEL,
        base_url=settings.GEMINI_BASE_URL,
        timeout_seconds=float(settings.GEMINI_TIMEOUT_SECONDS),
    )


async def get_gemini_client() -> GeminiClient:
    from app.infrastructure.http.manager import HTTPClientManager

    http_client = await HTTPClientManager.get()
    return GeminiClient(
        http=http_client,
        config=build_gemini_config(),
    )
