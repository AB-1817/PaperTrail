from __future__ import annotations

import json
from datetime import datetime, timezone

import structlog

from app.core.config import get_settings
from app.ingestion.normalizer import normalize_doi, strip_markup
from app.providers.base import (
    NormalizedAuthor,
    NormalizedPaper,
    family_name_from,
)
from app.providers.http import MemoryCache, ProviderHTTP, limiter_for

logger = structlog.get_logger(__name__)


class SemanticScholarAdapter:
    name = "semantic_scholar"

    def __init__(self, cache: MemoryCache | None = None) -> None:
        settings = get_settings()
        limiter_key = "semantic_scholar_keyed" if settings.semantic_scholar_api_key else "semantic_scholar"
        self.http = ProviderHTTP(
            name=self.name,
            limiter=limiter_for(limiter_key),
            cache=cache or MemoryCache(),
        )

    async def search(self, query: str, limit: int = 20) -> list[NormalizedPaper]:
        settings = get_settings()
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        fields = "paperId,externalIds,title,abstract,authors,year,venue,openAccessPdf,fieldsOfStudy"
        params = {
            "query": query,
            "limit": str(min(limit, 50)),
            "fields": fields,
        }
        headers = {}
        if settings.semantic_scholar_api_key:
            headers["x-api-key"] = settings.semantic_scholar_api_key

        try:
            raw_text = await self.http.get_text(url, params=params, headers=headers)
            data = json.loads(raw_text)
        except Exception as exc:
            logger.error("semantic_scholar_search_failed", query=query, error=str(exc))
            return []

        papers: list[NormalizedPaper] = []
        for item in data.get("data", []):
            try:
                paper = self._parse_item(item)
                if paper:
                    papers.append(paper)
            except Exception as exc:
                logger.warning("semantic_scholar_parse_error", error=str(exc))
        return papers

    def _parse_item(self, item: dict) -> NormalizedPaper | None:
        title = strip_markup(item.get("title") or "")
        if not title:
            return None

        ext_ids = item.get("externalIds") or {}
        doi = normalize_doi(ext_ids.get("DOI"))

        authors: list[NormalizedAuthor] = []
        for pos, auth in enumerate(item.get("authors") or [], start=1):
            name = auth.get("name") or "Unknown"
            authors.append(
                NormalizedAuthor(
                    name=name,
                    family_name=family_name_from(name),
                    orcid=None,
                    institution=None,
                    position=pos,
                )
            )

        topics = item.get("fieldsOfStudy") or []
        abstract = strip_markup(item.get("abstract"))

        oa_pdf = item.get("openAccessPdf") or {}
        oa_url = oa_pdf.get("url")
        is_oa = oa_url is not None

        return NormalizedPaper(
            doi=doi,
            title=title,
            abstract=abstract,
            year=item.get("year"),
            venue=item.get("venue"),
            volume=None,
            issue=None,
            pages=None,
            open_access=is_oa,
            oa_url=oa_url,
            access_license=None,
            authors=authors,
            topics=topics,
            reference_dois=[],
            source_provider=self.name,
            provider_id=str(item.get("paperId", "")),
            raw_metadata=item,
            fetched_at=datetime.now(timezone.utc),
            has_abstract=abstract is not None,
            has_references=False,
            has_full_text_url=oa_url is not None,
        )
