from __future__ import annotations

import time
from typing import Any

import httpx
import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)

_CACHE_TTL_SECONDS = 86400  # 24 hours


class JWKSClient:
    def __init__(self) -> None:
        self._keys: list[dict[str, Any]] = []
        self._fetched_at: float = 0.0

    @property
    def _jwks_url(self) -> str:
        settings = get_settings()
        return f"{settings.supabase_jwt_issuer}/.well-known/jwks.json"

    async def _fetch(self) -> None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(self._jwks_url)
            resp.raise_for_status()
            data = resp.json()
            self._keys = data.get("keys", [])
            self._fetched_at = time.monotonic()
            logger.info("jwks_refreshed", key_count=len(self._keys))

    async def get_keys(self, force_refresh: bool = False) -> list[dict[str, Any]]:
        age = time.monotonic() - self._fetched_at
        if force_refresh or not self._keys or age > _CACHE_TTL_SECONDS:
            await self._fetch()
        return self._keys


# Module-level singleton — shared across all requests
jwks_client = JWKSClient()
