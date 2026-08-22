from pydantic import BaseModel, ConfigDict, Field


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=lambda name: "".join(
            word.title() if i else word
            for i, word in enumerate(name.split("_"))
        ),
        populate_by_name=True,
    )


class GeminiUsageMetadata(CamelModel):
    prompt_token_count: int = 0
    candidates_token_count: int = 0
    total_token_count: int = 0


class GeminiCandidate(CamelModel):
    text: str
    finish_reason: str | None = None


class GeminiGenerateResponse(CamelModel):
    text: str
    model_version: str | None = None
    usage: GeminiUsageMetadata = Field(
        default_factory=GeminiUsageMetadata,
    )
