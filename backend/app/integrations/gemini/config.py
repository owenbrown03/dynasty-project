from pydantic import BaseModel


class GeminiConfig(BaseModel):
    api_key: str | None = None
    model: str = "gemini-flash-latest"
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    timeout_seconds: float = 60.0
