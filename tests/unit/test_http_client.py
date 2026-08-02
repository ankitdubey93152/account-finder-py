import pytest
import respx
from httpx import Response
from core.http_client import AsyncHTTPClient
from core.exceptions import RateLimitedError, PlatformUnavailableError

@pytest.mark.asyncio
async def test_async_http_client_successful_request():
    with respx.mock:
        respx.get("https://api.example.com/test").mock(
            return_value=Response(200, json={"status": "ok"})
        )
        client = AsyncHTTPClient()
        response = await client.request("GET", "https://api.example.com/test")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        await client.close()

@pytest.mark.asyncio
async def test_async_http_client_429_rate_limit():
    with respx.mock:
        respx.get("https://api.example.com/rate-limited").mock(
            return_value=Response(429, text="Too Many Requests")
        )
        client = AsyncHTTPClient(max_retries=1)
        with pytest.raises(RateLimitedError):
            await client.request("GET", "https://api.example.com/rate-limited")
        await client.close()

@pytest.mark.asyncio
async def test_async_http_client_server_error_retry():
    with respx.mock:
        route = respx.get("https://api.example.com/flaky").mock(
            side_effect=[
                Response(503, text="Service Unavailable"),
                Response(200, json={"result": "success"}),
            ]
        )
        client = AsyncHTTPClient(max_retries=2)
        response = await client.request("GET", "https://api.example.com/flaky")
        assert response.status_code == 200
        assert response.json() == {"result": "success"}
        assert route.call_count == 2
        await client.close()
