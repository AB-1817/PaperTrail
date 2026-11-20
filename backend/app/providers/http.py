from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

import httpx
import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

logger = structlog.get_logger(__name__)


class MemoryCache:
    def __init__(self) -> None:
        self._items: dict[str, tuple[float, str]] = {}

    def get(self, key: str) -> str | None:
        item = self._items.get(key)
        if item is None:
            return None
        expires, value = item
        if expires < time.monotonic():
            self._items.pop(key, None)
            return None
        return value

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        self._items[key] = (time.monotonic() + ttl_seconds, value)


@dataclass
class FixedWindowLimiter:
    """In-process limiter used by a single API worker. Limits are [U] until verified."""

    max_calls: int
    period_seconds: float
    events: list[float] = field(default_factory=list)

    def allow(self, now: float | None = None) -> bool:
        current = time.monotonic() if now is None else now
        self.events = [stamp for stamp in self.events if current - stamp < self.period_seconds]
        if len(self.events) >= self.max_calls:
            return False
        self.events.append(current)
        return True

    def retry_after(self, now: float | None = None) -> float:
        current = time.monotonic() if now is None else now
        if not self.events:
            return 0.0
        return max(0.0, self.period_seconds - (current - self.events[0]))


# Per-provider ceilings from the blueprint. Treat as unverified until checked.
PROVIDER_LIMITS: dict[str, tuple[int, float]] = {
    "openalex": (10, 1.0),
    "semantic_scholar": (1, 1.0),
    "semantic_scholar_keyed": (10, 1.0),
    "arxiv": (3, 1.0),
    "crossref": (50, 1.0),
    "unpaywall": (10, 1.0),
}


def limiter_for(provider: str) -> FixedWindowLimiter:
    max_calls, period = PROVIDER_LIMITS[provider]
    return FixedWindowLimiter(max_calls=max_calls, period_seconds=period)


class ProviderHTTP:
    def __init__(self, name: str, limiter: FixedWindowLimiter, cache: MemoryCache) -> None:
        self.name = name
        self.limiter = limiter
        self.cache = cache

    async def get_text(
        self,
        url: str,
        params: dict[str, str],
        headers: dict[str, str] | None = None,
        ttl_seconds: int = 3600,
    ) -> str:
        key = url + "|" + "&".join(f"{k}={params[k]}" for k in sorted(params))
        cached = self.cache.get(key)
        if cached is not None:
            logger.info("provider_cache_hit", provider=self.name)
            return cached
        await self._acquire()
        body = await self._fetch(url, params, headers or {})
        self.cache.set(key, body, ttl_seconds)
        return body

    async def _acquire(self) -> None:
        if self.limiter.allow():
            return
        logger.warning("rate_limit_blocked", provider=self.name)
        await asyncio.sleep(self.limiter.retry_after())
        if self.limiter.allow():
            return
        logger.warning("rate_limit_blocked", provider=self.name)
        from app.providers.base import RateLimited

        raise RateLimited(self.name)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=0.2, max=4),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True,
    )
    async def _fetch(self, url: str, params: dict[str, str], headers: dict[str, str]) -> str:
        started = time.perf_counter()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
        logger.info(
            "provider_request",
            provider=self.name,
            endpoint=url,
            status_code=response.status_code,
            latency_ms=round((time.perf_counter() - started) * 1000, 1),
        )
        return response.text
