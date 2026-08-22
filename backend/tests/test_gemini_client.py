import asyncio
import json

import httpx
import pytest

from app.integrations.gemini.client import GeminiClient
from app.integrations.gemini.config import GeminiConfig


def _gemini_ok_payload() -> dict:
    return {
        "candidates": [
            {
                "finishReason": "STOP",
                "content": {
                    "parts": [
                        {"text": "Hello "},
                        {"text": "world"},
                    ]
                },
            }
        ],
        "modelVersion": "gemini-2.5-flash",
        "usageMetadata": {
            "promptTokenCount": 10,
            "candidatesTokenCount": 5,
            "totalTokenCount": 15,
        },
    }


def _client_with_handler(
    handler,
    api_key: str | None = "test-key",
    **config_kwargs,
) -> GeminiClient:
    return GeminiClient(
        http=httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
        ),
        config=GeminiConfig(
            api_key=api_key,
            retry_backoff_seconds=0,
            **config_kwargs,
        ),
    )


def test_generate_text_parses_parts_and_usage():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)

        return httpx.Response(200, json=_gemini_ok_payload())

    client = _client_with_handler(handler)

    text = asyncio.run(
        client.read.generate_text(
            "Say hello",
            system_instruction="Be terse",
        )
    )

    assert text == "Hello world"
    assert "models/gemini-flash-latest:generateContent" in captured["url"]
    assert "key=test-key" in captured["url"]
    assert (
        captured["body"]["systemInstruction"]["parts"][0]["text"]
        == "Be terse"
    )
    assert captured["body"]["contents"][0]["parts"][0]["text"] == "Say hello"


def test_generate_content_returns_usage_metadata():
    async def run():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200,
                    json=_gemini_ok_payload(),
                )
            )
        ) as http:
            client = GeminiClient(
                http=http,
                config=GeminiConfig(api_key="k"),
            )

            return await client.transport.generate_content(
                contents=[
                    {"role": "user", "parts": [{"text": "hi"}]},
                ],
            )

    response = asyncio.run(run())

    assert response.model_version == "gemini-2.5-flash"
    assert response.usage.total_token_count == 15


def test_generate_handles_empty_candidates():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"candidates": []})

    client = _client_with_handler(handler)

    text = asyncio.run(client.read.generate_text("hi"))

    assert text == ""


def test_missing_api_key_raises():
    client = _client_with_handler(
        lambda request: httpx.Response(500),
        api_key=None,
    )

    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        asyncio.run(client.read.generate_text("hi"))


def test_http_error_propagates():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": "rate limited"})

    client = _client_with_handler(handler)

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(client.read.generate_text("hi"))


def test_retries_transient_errors_then_succeeds():
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        if len(calls) < 3:
            return httpx.Response(503, json={"error": "overloaded"})
        return httpx.Response(200, json=_gemini_ok_payload())

    client = _client_with_handler(
        handler,
        max_attempts=3,
    )

    text = asyncio.run(client.read.generate_text("hi"))

    assert text == "Hello world"
    assert len(calls) == 3


def test_non_retryable_error_raises_without_retry():
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(400, json={"error": "bad request"})

    client = _client_with_handler(
        handler,
        max_attempts=3,
    )

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(client.read.generate_text("hi"))

    assert len(calls) == 1


def test_gives_up_after_max_attempts():
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(503, json={"error": "overloaded"})

    client = _client_with_handler(
        handler,
        max_attempts=2,
    )

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(client.read.generate_text("hi"))

    assert len(calls) == 2


def test_honors_retry_after_header():
    import time

    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(time.monotonic())
        if len(calls) == 1:
            return httpx.Response(
                429,
                json={"error": {"status": "RESOURCE_EXHAUSTED"}},
                headers={"Retry-After": "1"},
            )
        return httpx.Response(200, json=_gemini_ok_payload())

    client = _client_with_handler(
        handler,
        max_attempts=2,
    )

    text = asyncio.run(client.read.generate_text("hi"))

    assert text == "Hello world"
    assert len(calls) == 2
    waited = calls[1] - calls[0]
    assert waited >= 0.9


def test_honors_retry_info_detail_delay():
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(
                429,
                json={
                    "error": {
                        "code": 429,
                        "status": "RESOURCE_EXHAUSTED",
                        "details": [
                            {
                                "@type": (
                                    "type.googleapis.com/"
                                    "google.rpc.RetryInfo"
                                ),
                                "retryDelay": "1s",
                            }
                        ],
                    }
                },
            )
        return httpx.Response(200, json=_gemini_ok_payload())

    client = _client_with_handler(
        handler,
        max_attempts=2,
    )

    text = asyncio.run(client.read.generate_text("hi"))

    assert text == "Hello world"
    assert len(calls) == 2
