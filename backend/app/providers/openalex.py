from __future__ import annotations

import json
from datetime import datetime, timezone

import structlog

from app.core.config import get_settings
from app.ingestion.normalizer import (
    normalize_doi,
    reconstruct_inverted_abstract,
    strip_markup,
)
from app.providers.base import (
    NormalizedAuthor,
    NormalizedPaper,
    family_name_from,
)
from app.providers.http import MemoryCache, ProviderHTTP, limiter_for

logger = structlog.get_logger(__name__)


class OpenAlexAdapter:
    name = "openalex"

    def __init__(self, cache: MemoryCache | None = None) -> None:
        self.http = ProviderHTTP(
            name=self.name,
            limiter=limiter_for(self.name),
            cache=cache or MemoryCache(),
        )

    async def search(self, query: str, limit: int = 20) -> list[NormalizedPaper]:
        settings = get_settings()
        url = "https://api.openalex.org/works"
        params: dict[str, str] = {
            "search": query,
            "per-page": str(min(limit, 50)),
        }
        if settings.openalex_email:
            params["mailto"] = settings.openalex_email

        try:
            raw_text = await self.http.get_text(url, params=params)
            data = json.loads(raw_text)
        except Exception as exc:
            logger.error("openalex_search_failed", query=query, error=str(exc))
            return []

        results: list[NormalizedPaper] = []
        for item in data.get("results", []):
            try:
                paper = self._parse_work(item)
                results.append(paper)
            except Exception as exc:
                logger.warning("openalex_work_parse_error", work_id=item.get("id"), error=str(exc))
        return results

    def _parse_work(self, item: dict) -> NormalizedPaper:
        doi = normalize_doi(item.get("doi"))
        title = strip_markup(item.get("title") or "Untitled")

        # Abstract
        abstract_inverted = item.get("abstract_inverted_index")
        abstract = reconstruct_inverted_abstract(abstract_inverted)

        # Year
        year = item.get("publication_year")

        # Authors
        authors: list[NormalizedAuthor] = []
        for authorship in item.get("authorships", []):
            author_data = authorship.get("author", {})
            name = author_data.get("display_name") or "Unknown"
            orcid = author_data.get("orcid")
            pos = authorship.get("author_position", "")
            # determine position number
            position = 1 if pos == "first" else (len(authors) + 1)
            inst_list = authorship.get("institutions", [])
            institution = inst_list[0].get("display_name") if inst_list else None

            authors.append(
                NormalizedAuthor(
                    name=name,
                    family_name=family_name_from(name),
                    orcid=orcid,
                    institution=institution,
                    position=position,
                )
            )

        # Topics / concepts
        topics: list[str] = []
        for concept in item.get("concepts", []):
            if concept.get("display_name"):
                topics.append(concept["display_name"])

        # OA info
        oa_info = item.get("open_access", {})
        is_oa = bool(oa_info.get("is_oa", False))
        oa_url = oa_info.get("oa_url")
        license_str = oa_info.get("license")

        # References
        referenced_works = [normalize_doi(r) for r in item.get("referenced_works", []) if r]
        clean_refs = [r for r in referenced_works if r]

        # Venue
        biblio = item.get("biblio", {})
        venue = item.get("primary_location", {}).get("source", {}).get("display_name")

        return NormalizedPaper(
            doi=doi,
            title=title,
            abstract=abstract,
            year=year,
            venue=venue,
            volume=biblio.get("volume"),
            issue=biblio.get("issue"),
            pages=None,
            open_access=is_oa,
            oa_url=oa_url,
            access_license=license_str,
            authors=authors,
            topics=topics,
            reference_dois=clean_refs,
            source_provider=self.name,
            provider_id=str(item.get("id", "")),
            raw_metadata=item,
            fetched_at=datetime.now(timezone.utc),
            has_abstract=abstract is not None,
            has_references=len(clean_refs) > 0,
            has_full_text_url=oa_url is not None,
        )
