from httpx import Response
import pytest
import respx

from core.http_client import AsyncHTTPClient
from modules.username_search.detector import check_platform
from modules.username_search.platforms import PlatformSpec


@pytest.mark.asyncio
@pytest.mark.parametrize(("spec", "response", "expected"), [
    (PlatformSpec(name="status", url_template="https://test.example/{username}", check_method="status_code"), Response(200), True),
    (PlatformSpec(name="match", url_template="https://test.example/{username}", check_method="text_match", existence_indicator="profile-found"), Response(200, text="profile-found"), True),
    (PlatformSpec(name="absence", url_template="https://test.example/{username}", check_method="text_absence", absence_indicator="Page Not Found"), Response(200, text="Page Not Found"), False),
    (PlatformSpec(name="json", url_template="https://test.example/{username}", check_method="json_field", json_exists_path="data.name"), Response(200, json={"data": {"name": "alice"}}), True),
])
async def test_detector_methods(spec, response, expected):
    with respx.mock:
        respx.get("https://test.example/alice").mock(return_value=response)
        client = AsyncHTTPClient()
        result = await check_platform(client, spec, "alice")
        await client.close()
    assert result.exists is expected
    assert result.confidence == "high"


@pytest.mark.asyncio
async def test_detector_json_missing_expected_key_is_inconclusive():
    spec = PlatformSpec(name="json", url_template="https://test.example/{username}", check_method="json_field", json_exists_path="data.name")
    with respx.mock:
        respx.get("https://test.example/alice").mock(return_value=Response(200, json={"data": {}}))
        client = AsyncHTTPClient()
        result = await check_platform(client, spec, "alice")
        await client.close()
    assert result.exists is None
    assert result.confidence == "low"


@pytest.mark.asyncio
async def test_detector_server_error_is_inconclusive():
    spec = PlatformSpec(name="status", url_template="https://test.example/{username}", check_method="status_code")
    with respx.mock:
        respx.get("https://test.example/alice").mock(return_value=Response(503))
        client = AsyncHTTPClient(max_retries=0)
        result = await check_platform(client, spec, "alice")
        await client.close()
    assert result.exists is None
