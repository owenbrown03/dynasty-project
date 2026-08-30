import asyncio
import httpx
import pytest

from app.infrastructure.http.retry import retry

def test_retry_catches_transport_error():
    async def _test():
        attempts = 0

        async def fail_then_succeed():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise httpx.RemoteProtocolError("Server disconnected without sending a response", request=httpx.Request("GET", "http://test"))
            return "success"

        result = await retry(fail_then_succeed, retries=4, base_delay=0.01, max_delay=0.05)
        
        assert result == "success"
        assert attempts == 3

    asyncio.run(_test())

def test_retry_raises_after_max_retries():
    async def _test():
        attempts = 0

        async def always_fail():
            nonlocal attempts
            attempts += 1
            raise httpx.RemoteProtocolError("Server disconnected without sending a response", request=httpx.Request("GET", "http://test"))

        with pytest.raises(httpx.RemoteProtocolError):
            await retry(always_fail, retries=3, base_delay=0.01, max_delay=0.05)
        
        assert attempts == 3

    asyncio.run(_test())

def test_retry_catches_other_transport_errors():
    async def _test():
        attempts = 0

        async def fail_then_succeed():
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise httpx.ConnectTimeout("Connect timeout", request=httpx.Request("GET", "http://test"))
            if attempts == 2:
                raise httpx.ReadTimeout("Read timeout", request=httpx.Request("GET", "http://test"))
            return "success"

        result = await retry(fail_then_succeed, retries=4, base_delay=0.01, max_delay=0.05)
        
        assert result == "success"
        assert attempts == 3

    asyncio.run(_test())
