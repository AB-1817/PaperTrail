from __future__ import annotations

import json
from datetime import datetime, timezone

import structlog

from app.core.config import get_settings
from app.ingestion.normalizer import (
    normalize_doi,
    strip_markup,
    year_from_date_parts,
)
from app.providers.base import (
    NormalizedAuthor,
    NormalizedPaper,
    family_name_from,
)
from app.providers.http import MemoryCache, ProviderHTTP, limiter_for

logger = structlog.get_logger(__name__)


class CrossrefAdapter:
    name = "crossref"

    def __init__(self, cache: MemoryCache | None = None) -> None:
        self.http = ProviderHTTP(
            name=self.name,
            limiter=limiter_for(self.name),
            cache=cache or MemoryCache(),
        )

    async def search(self, query: str, limit: int = 20) -> list[NormalizedPaper]:
        settings = get_settings()
        url = "https://api.crossref.org/works"
        params = {
            "query": query,
            "rows": str(min(limit, 50)),
        }
        if settings.crossref_email:
            params["mailto"] = settings.crossref_email

        try:
            raw_text = await self.http.get_text(url, params=params)
            data = json.loads(raw_text)
        except Exception as exc:
            logger.error("crossref_search_failed", query=query, error=str(exc))
            return []

        papers: list[NormalizedPaper] = []
        for item in data.get("message", {}).get("items", []):
            try:
                paper = self._parse_item(item)
                if paper:
                    papers.append(paper)
            except Exception as exc:
                logger.warning("crossref_item_parse_error", error=str(exc))
        return papers

    async def get_by_doi(self, doi: str) -> NormalizedPaper | None:
        normalized = normalize_doi(doi)
        if not normalized:
            return None
        settings = get_settings()
        url = f"https://api.crossref.org/works/{normalized}"
        params: dict[str, str] = {}
        if settings.crossref_email:
            params["mailto"] = settings.crossref_email
        try:
            raw_text = await self.http.get_text(url, params=params)
            data = json.loads(raw_text)
            item = data.get("message") or {}
            return self._parse_item(item)
        except Exception as exc:
            logger.warning("crossref_doi_lookup_failed", doi=normalized, error=str(exc))
            return None

    def _parse_item(self, item: dict) -> NormalizedPaper | None:
        titles = item.get("title") or []
        if not titles:
            return None
        title = strip_markup(titles[0])

        doi = normalize_doi(item.get("DOI"))
        abstract = strip_markup(item.get("abstract"))

        # Year from published date
        issued = item.get("issued", {}).get("date-parts")
        year = year_from_date_parts(issued)

        # Authors
        authors: list[NormalizedAuthor] = []
        for pos, auth in enumerate(item.get("author") or [], start=1):
            given = auth.get("given", "")
            family = auth.get("family", "")
            name = f"{given} {family}".strip() or "Unknown"
            orcid = auth.get("ORCID")
            authors.append(
                NormalizedAuthor(
                    name=name,
                    family_name=family or family_name_from(name),
                    orcid=orcid,
                    institution=None,
                    position=pos,
                )
            )

        venues = item.get("container-title") or []
        venue = venues[0] if venues else None

        return NormalizedPaper(
            doi=doi,
            title=title,
            abstract=abstract,
            year=year,
            venue=venue,
            volume=item.get("volume"),
            issue=item.get("issue"),
            pages=item.get("page"),
            open_access=False,
            oa_url=None,
            access_license=None,
            authors=authors,
            topics=[],
            reference_dois=[],
            source_provider=self.name,
            provider_id=str(doi or item.get("DOI", "")),
            raw_metadata=item,
            fetched_at=datetime.now(timezone.utc),
            has_abstract=abstract is not None,
            has_references=False,
            has_full_text_url=False,
        )
