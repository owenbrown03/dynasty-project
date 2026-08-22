from pydantic import BaseModel


class GeminiConfig(BaseModel):
    api_key: str | None = None
    model: str = "gemini-flash-latest"
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    timeout_seconds: float = 60.0
    max_attempts: int = 3
    retry_backoff_seconds: float = 1.0
