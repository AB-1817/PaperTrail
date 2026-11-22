from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import structlog

from app.ingestion.normalizer import normalize_doi, strip_markup
from app.providers.base import (
    NormalizedAuthor,
    NormalizedPaper,
    family_name_from,
)
from app.providers.http import MemoryCache, ProviderHTTP, limiter_for

logger = structlog.get_logger(__name__)

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


class ArXivAdapter:
    name = "arxiv"

    def __init__(self, cache: MemoryCache | None = None) -> None:
        self.http = ProviderHTTP(
            name=self.name,
            limiter=limiter_for(self.name),
            cache=cache or MemoryCache(),
        )

    async def search(self, query: str, limit: int = 20) -> list[NormalizedPaper]:
        url = "https://export.arxiv.org/api/query"
        clean_q = re.sub(r"[^\w\s]", " ", query).strip()
        params = {
            "search_query": f"all:{clean_q}",
            "max_results": str(min(limit, 50)),
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        try:
            raw_xml = await self.http.get_text(url, params=params)
            root = ET.fromstring(raw_xml)
        except Exception as exc:
            logger.error("arxiv_search_failed", query=query, error=str(exc))
            return []

        papers: list[NormalizedPaper] = []
        for entry in root.findall("atom:entry", ATOM_NS):
            try:
                paper = self._parse_entry(entry)
                if paper:
                    papers.append(paper)
            except Exception as exc:
                logger.warning("arxiv_entry_parse_error", error=str(exc))
        return papers

    async def get_by_id(self, arxiv_id: str) -> NormalizedPaper | None:
        clean_id = arxiv_id.strip().lower()
        if clean_id.startswith("arxiv:"):
            clean_id = clean_id[len("arxiv:") :]
        clean_id = clean_id.split("v")[0]
        url = "https://export.arxiv.org/api/query"
        params = {
            "id_list": clean_id,
            "max_results": "1",
        }
        try:
            raw_xml = await self.http.get_text(url, params=params)
            root = ET.fromstring(raw_xml)
            entry = root.find("atom:entry", ATOM_NS)
            if entry is None:
                return None
            return self._parse_entry(entry)
        except Exception as exc:
            logger.warning("arxiv_id_lookup_failed", arxiv_id=clean_id, error=str(exc))
            return None

    def _parse_entry(self, entry: ET.Element) -> NormalizedPaper | None:
        raw_id = entry.findtext("atom:id", default="", namespaces=ATOM_NS).strip()
        if not raw_id:
            return None

        # Arxiv identifier e.g. "http://arxiv.org/abs/2301.00001v1" -> "2301.00001"
        arxiv_id = raw_id.split("/abs/")[-1].split("v")[0]

        title = strip_markup(entry.findtext("atom:title", default="Untitled", namespaces=ATOM_NS))
        title = re.sub(r"\s+", " ", title).strip()

        abstract = entry.findtext("atom:summary", default="", namespaces=ATOM_NS)
        abstract = strip_markup(abstract)

        published_str = entry.findtext("atom:published", default="", namespaces=ATOM_NS)
        year: int | None = None
        if published_str and len(published_str) >= 4:
            try:
                year = int(published_str[:4])
            except ValueError:
                pass

        doi = normalize_doi(entry.findtext("arxiv:doi", default="", namespaces=ATOM_NS))

        authors: list[NormalizedAuthor] = []
        for pos, author_elem in enumerate(entry.findall("atom:author", ATOM_NS), start=1):
            name = author_elem.findtext("atom:name", default="", namespaces=ATOM_NS).strip()
            if name:
                authors.append(
                    NormalizedAuthor(
                        name=name,
                        family_name=family_name_from(name),
                        orcid=None,
                        institution=None,
                        position=pos,
                    )
                )

        topics: list[str] = []
        for cat in entry.findall("atom:category", ATOM_NS):
            term = cat.attrib.get("term")
            if term:
                topics.append(term)

        oa_url = f"https://arxiv.org/pdf/{arxiv_id}"

        return NormalizedPaper(
            doi=doi,
            title=title,
            abstract=abstract,
            year=year,
            venue="arXiv",
            volume=None,
            issue=None,
            pages=None,
            open_access=True,
            oa_url=oa_url,
            access_license="arxiv-non-exclusive",
            authors=authors,
            topics=topics,
            reference_dois=[],
            source_provider=self.name,
            provider_id=arxiv_id,
            raw_metadata={"raw_id": raw_id, "arxiv_id": arxiv_id},
            fetched_at=datetime.now(timezone.utc),
            has_abstract=bool(abstract),
            has_references=False,
            has_full_text_url=True,
        )
