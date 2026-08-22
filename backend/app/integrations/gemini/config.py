from pydantic import BaseModel


class GeminiConfig(BaseModel):
    api_key: str | None = None
    model: str = "gemini-3.5-flash"
    model_fallbacks: tuple[str, ...] = ("gemini-3.1-flash-lite",)
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    timeout_seconds: float = 60.0
    max_attempts: int = 3
    retry_backoff_seconds: float = 1.0

    @property
    def model_chain(self) -> tuple[str, ...]:
        """Primary model followed by deduplicated fallbacks, in order."""
        seen: dict[str, None] = {self.model: None}
        for fallback in self.model_fallbacks:
            seen.setdefault(fallback, None)
        return tuple(seen)
