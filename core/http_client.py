import asyncio
import httpx
import structlog
from typing import Any, Mapping
from core.config import settings
from core.exceptions import RateLimitedError, PlatformUnavailableError
from core.rate_limiter import rate_limiter

logger = structlog.get_logger(__name__)

class AsyncHTTPClient:
    """Shared async HTTP client with retry logic, exponential backoff, and rate-limit safety."""

    def __init__(
        self,
        timeout: float = settings.DEFAULT_TIMEOUT_SECONDS,
        headers: Mapping[str, str] | None = None,
        max_retries: int = 2,
    ) -> None:
        default_headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        if headers:
            default_headers.update(headers)

        self.timeout = timeout
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None
        self.default_headers = default_headers

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers=self.default_headers,
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def request(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str] | None = None,
        params: Mapping[str, Any] | None = None,
        min_delay_seconds: float = 0.5,
        **kwargs: Any,
    ) -> httpx.Response:
        client = await self.get_client()
        request_headers = dict(self.default_headers)
        if headers:
            request_headers.update(headers)

        retries = 0
        backoff_delay = 1.0
        host = httpx.URL(url).host
        if not host:
            raise ValueError(f"URL has no host: {url}")

        while True:
            try:
                async with rate_limiter.limited(host, min_delay_seconds):
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=request_headers,
                        params=params,
                        **kwargs,
                    )

                if response.status_code == 429:
                    logger.warning("Rate limited (HTTP 429)", url=url, retries=retries)
                    if retries < self.max_retries:
                        await asyncio.sleep(backoff_delay)
                        retries += 1
                        backoff_delay *= 2
                        continue
                    raise RateLimitedError(f"Rate limited by target URL: {url}")

                # Retry on transient server errors (5xx)
                if 500 <= response.status_code < 600:
                    if retries < self.max_retries:
                        logger.warning(
                            "Transient server error",
                            status_code=response.status_code,
                            url=url,
                            retries=retries,
                        )
                        await asyncio.sleep(backoff_delay)
                        retries += 1
                        backoff_delay *= 2
                        continue

                return response

            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                if retries < self.max_retries:
                    logger.warning(
                        "Network error/timeout",
                        error=str(exc),
                        url=url,
                        retries=retries,
                    )
                    await asyncio.sleep(backoff_delay)
                    retries += 1
                    backoff_delay *= 2
                    continue
                raise PlatformUnavailableError(
                    f"Failed to connect to {url}: {str(exc)}", detail=str(exc)
                ) from exc
