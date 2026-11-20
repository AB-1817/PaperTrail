from __future__ import annotations

import json

import structlog

from app.core.config import get_settings
from app.ingestion.normalizer import normalize_doi
from app.providers.base import OALocation
from app.providers.http import MemoryCache, ProviderHTTP, limiter_for

logger = structlog.get_logger(__name__)


class UnpaywallAdapter:
    name = "unpaywall"

    def __init__(self, cache: MemoryCache | None = None) -> None:
        self.http = ProviderHTTP(
            name=self.name,
            limiter=limiter_for(self.name),
            cache=cache or MemoryCache(),
        )

    async def fetch_oa(self, raw_doi: str) -> OALocation | None:
        doi = normalize_doi(raw_doi)
        if not doi:
            return None

        settings = get_settings()
        email = settings.unpaywall_email or "research@papertrail.local"
        url = f"https://api.unpaywall.org/v2/{doi}"
        params = {"email": email}

        try:
            raw_text = await self.http.get_text(url, params=params, ttl_seconds=86400)
            data = json.loads(raw_text)
        except Exception as exc:
            logger.warning("unpaywall_fetch_failed", doi=doi, error=str(exc))
            return None

        is_oa = bool(data.get("is_oa", False))
        best_oa = data.get("best_oa_location") or {}
        pdf_url = best_oa.get("url_for_pdf") or best_oa.get("url")
        license_str = best_oa.get("license")

        return OALocation(
            doi=doi,
            is_oa=is_oa,
            pdf_url=pdf_url,
            license=license_str,
        )
