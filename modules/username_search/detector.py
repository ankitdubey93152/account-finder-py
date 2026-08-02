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
        return PlatformResult(
            platform=spec.name,
            url=url,
            exists=None,
            confidence="low",
            error=str(exc),
            checked_at=datetime.now(timezone.utc),
            response_time_ms=int((time.monotonic() - start) * 1000),
        )

    elapsed_ms = int((time.monotonic() - start) * 1000)
    exists, confidence, error_msg = _evaluate(spec, response)
    logger.debug("username platform checked", platform=spec.name, status_code=response.status_code, exists=exists)
    return PlatformResult(
        platform=spec.name,
        url=url,
        exists=exists,
        confidence=confidence,
        response_time_ms=elapsed_ms,
        checked_at=datetime.now(timezone.utc),
        error=error_msg,
    )


def _evaluate(spec: PlatformSpec, response: object) -> tuple[bool | None, str, str | None]:
    status_code = getattr(response, "status_code", 0)

    if 500 <= status_code < 600:
        return None, "low", f"Target server error (HTTP {status_code})"
    if status_code in (401, 403):
        return None, "low", f"Access blocked / WAF challenge (HTTP {status_code})"
    if status_code == 429:
        return None, "low", "Rate limit exceeded (HTTP 429)"

    if spec.check_method == "status_code":
        if status_code == spec.expected_status:
            return True, "high", None
        elif status_code == 404:
            return False, "high", None
        else:
            return None, "low", f"Unexpected status {status_code}"

    if status_code == 404:
        return False, "high", None

    if spec.check_method == "text_absence":
        if status_code != spec.expected_status:
            return None, "low", f"Unexpected status {status_code}"
        text = getattr(response, "text", "")
        if (spec.absence_indicator or "") in text:
            return False, "high", None
        return True, "high", None

    if spec.check_method == "text_match":
        if status_code != spec.expected_status:
            return None, "low", f"Unexpected status {status_code}"
        text = getattr(response, "text", "")
        if re.search(spec.existence_indicator or "", text):
            return True, "high", None
        return False, "high", None

    if spec.check_method == "json_field":
        if status_code != spec.expected_status:
            return None, "low", f"Unexpected status {status_code}"
        try:
            value = response.json()
            for part in (spec.json_exists_path or "").split("."):
                value = value[part]
            if value is not None:
                return True, "high", None
            return False, "high", None
        except (KeyError, TypeError, ValueError):
            return None, "low", f"Field '{spec.json_exists_path}' missing or invalid JSON"

    return None, "low", f"Unexpected status {status_code}"
