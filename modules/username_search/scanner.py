import asyncio
import re
import time

from core.config import settings
from core.exceptions import InvalidUsernameError, ScanTimeoutError
from core.http_client import AsyncHTTPClient
from modules.username_search.detector import check_platform
from modules.username_search.models import PlatformResult, ScanSummary
from modules.username_search.platforms import PLATFORMS, PlatformSpec

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")


async def scan_username(username: str, concurrency: int = 15) -> ScanSummary:
    if not username or not USERNAME_PATTERN.match(username) or len(username) > 64:
        raise InvalidUsernameError(
            f"Invalid username '{username}'. Must be 1-64 characters containing only alphanumeric, underscore, hyphen, or dot.",
            detail="Validation failed against pattern r'^[A-Za-z0-9_.-]+$'",
        )

    if concurrency < 1 or concurrency > 20:
        raise ValueError("Concurrency must be between 1 and 20.")

    start = time.monotonic()
    client = AsyncHTTPClient()
    semaphore = asyncio.Semaphore(concurrency)

    async def bounded_check(spec: PlatformSpec) -> PlatformResult:
        async with semaphore:
            return await check_platform(client, spec, username)

    try:
        tasks = [bounded_check(spec) for spec in PLATFORMS if spec.enabled]
        results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=settings.GLOBAL_SCAN_TIMEOUT_SECONDS)
    except (asyncio.TimeoutError, TimeoutError) as exc:
        raise ScanTimeoutError(
            f"Scan batch timed out after {settings.GLOBAL_SCAN_TIMEOUT_SECONDS}s",
            detail=str(exc),
        ) from exc
    finally:
        await client.close()

    return ScanSummary(
        username=username,
        total_platforms=len(results),
        found=sum(result.exists is True for result in results),
        not_found=sum(result.exists is False for result in results),
        errored=sum(result.exists is None for result in results),
        duration_ms=int((time.monotonic() - start) * 1000),
        results=results,
    )
