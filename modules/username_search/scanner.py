import asyncio
import time

from core.config import settings
from core.http_client import AsyncHTTPClient
from modules.username_search.detector import check_platform
from modules.username_search.models import PlatformResult, ScanSummary
from modules.username_search.platforms import PLATFORMS, PlatformSpec


async def scan_username(username: str, concurrency: int = 15) -> ScanSummary:
    if concurrency < 1:
        raise ValueError("concurrency must be at least 1")
    start = time.monotonic()
    client = AsyncHTTPClient()
    semaphore = asyncio.Semaphore(concurrency)

    async def bounded_check(spec: PlatformSpec) -> PlatformResult:
        async with semaphore:
            return await check_platform(client, spec, username)

    try:
        tasks = [bounded_check(spec) for spec in PLATFORMS if spec.enabled]
        results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=settings.GLOBAL_SCAN_TIMEOUT_SECONDS)
    finally:
        await client.close()

    return ScanSummary(username=username, total_platforms=len(results), found=sum(result.exists is True for result in results), not_found=sum(result.exists is False for result in results), errored=sum(result.exists is None for result in results), duration_ms=int((time.monotonic() - start) * 1000), results=results)
