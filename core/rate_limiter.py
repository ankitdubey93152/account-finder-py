import asyncio
import time
from contextlib import asynccontextmanager
from typing import Dict
from core.config import settings

class HostRateLimiter:
    """Per-host rate limiter using semaphores and timestamp windows."""

    def __init__(self, max_concurrent: int = settings.MAX_CONCURRENT_REQUESTS) -> None:
        self.global_semaphore = asyncio.Semaphore(max_concurrent)
        self.host_semaphores: Dict[str, asyncio.Semaphore] = {}
        self.host_last_request: Dict[str, float] = {}

    def get_host_semaphore(self, host: str, concurrent_per_host: int = 2) -> asyncio.Semaphore:
        if host not in self.host_semaphores:
            self.host_semaphores[host] = asyncio.Semaphore(concurrent_per_host)
        return self.host_semaphores[host]

    async def acquire(self, host: str, min_delay_seconds: float = 0.5) -> None:
        await self.global_semaphore.acquire()
        host_sem = self.get_host_semaphore(host)
        acquired_host = False
        try:
            await host_sem.acquire()
            acquired_host = True
            now = time.monotonic()
            last = self.host_last_request.get(host, 0.0)
            elapsed = now - last
            if elapsed < min_delay_seconds:
                await asyncio.sleep(min_delay_seconds - elapsed)
            self.host_last_request[host] = time.monotonic()
        except BaseException:
            # Cancellation during acquisition must not strand global capacity.
            if acquired_host:
                host_sem.release()
            self.global_semaphore.release()
            raise

    def release(self, host: str) -> None:
        if host in self.host_semaphores:
            self.host_semaphores[host].release()
        self.global_semaphore.release()

    @asynccontextmanager
    async def limited(self, host: str, min_delay_seconds: float = 0.5):
        """Acquire rate-limit capacity and always return it to the pool."""
        await self.acquire(host, min_delay_seconds)
        try:
            yield
        finally:
            self.release(host)

rate_limiter = HostRateLimiter()
