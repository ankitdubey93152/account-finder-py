import re
import time
from datetime import datetime, timezone

import structlog

from core.http_client import AsyncHTTPClient
from modules.username_search.models import PlatformResult
from modules.username_search.platforms import PlatformSpec

logger = structlog.get_logger(__name__)


async def check_platform(client: AsyncHTTPClient, spec: PlatformSpec, username: str) -> PlatformResult:
    url = spec.url_template.format(username=username)
    start = time.monotonic()
    try:
        response = await client.request("GET", url, headers=spec.headers, min_delay_seconds=spec.min_delay_seconds)
    except Exception as exc:
        return PlatformResult(platform=spec.name, url=url, exists=None, confidence="low", error=str(exc), checked_at=datetime.now(timezone.utc), response_time_ms=int((time.monotonic() - start) * 1000))

    elapsed_ms = int((time.monotonic() - start) * 1000)
    exists, confidence = _evaluate(spec, response)
    logger.debug("username platform checked", platform=spec.name, status_code=response.status_code, exists=exists)
    return PlatformResult(platform=spec.name, url=url, exists=exists, confidence=confidence, response_time_ms=elapsed_ms, checked_at=datetime.now(timezone.utc), error=None if exists is not None else f"Unexpected status {response.status_code}")


def _evaluate(spec: PlatformSpec, response: object) -> tuple[bool | None, str]:
    status_code = response.status_code
    if 500 <= status_code < 600:
        return None, "low"
    if spec.check_method == "status_code":
        return status_code == spec.expected_status, "high"
    if spec.check_method == "text_absence":
        if status_code != spec.expected_status:
            return None, "low"
        return (spec.absence_indicator or "") not in response.text, "high"
    if spec.check_method == "text_match":
        if status_code != spec.expected_status:
            return False, "high"
        return bool(re.search(spec.existence_indicator or "", response.text)), "high"
    if spec.check_method == "json_field":
        if status_code != spec.expected_status:
            return False, "high"
        try:
            value = response.json()
            for part in (spec.json_exists_path or "").split("."):
                value = value[part]
            return value is not None, "high"
        except (KeyError, TypeError, ValueError):
            return None, "low"
    return None, "low"
