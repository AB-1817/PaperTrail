"""
live_fetch.py
─────────────
Fetch a single paper from OpenAlex (by DOI) or arXiv (by arXiv ID),
persist it to the database, and return the PaperResponse dict.

Resilient: If DB persistence fails (e.g. DB offline or error),
it still returns the fetched paper so the user gets real live data.
"""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.normalizer import normalize_doi
from app.providers.arxiv import ArXivAdapter
from app.providers.base import NormalizedPaper
from app.providers.openalex import OpenAlexAdapter

logger = structlog.get_logger(__name__)

_ARXIV_ID_RE = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$|^[a-z\-]+/\d{7}$", re.IGNORECASE)


def _looks_like_arxiv_id(value: str) -> bool:
    cleaned = value.strip().lower()
    if cleaned.startswith("arxiv:"):
        cleaned = cleaned[6:]
    return bool(_ARXIV_ID_RE.match(cleaned))


def _looks_like_doi(value: str) -> bool:
    cleaned = value.strip().lower()
    if cleaned.startswith("doi:"):
        cleaned = cleaned[4:]
    return cleaned.startswith("10.") or "10." in cleaned


async def _persist(db: AsyncSession, paper: NormalizedPaper) -> str:
    """Insert paper into the DB (upsert on DOI) and return its UUID string."""
    paper_id = str(uuid.uuid4())
    doi = normalize_doi(paper.doi)

    try:
        await db.execute(
            text(
                """
                INSERT INTO papers
                    (id, doi, title, abstract, year, venue, volume, issue,
                     open_access, oa_url, has_abstract, has_references)
                VALUES
                    (:id, :doi, :title, :abstract, :year, :venue, :volume, :issue,
                     :oa, :oa_url, :has_abs, :has_refs)
                ON CONFLICT (doi) DO UPDATE
                    SET title        = EXCLUDED.title,
                        abstract     = COALESCE(EXCLUDED.abstract, papers.abstract),
                        year         = COALESCE(EXCLUDED.year,     papers.year),
                        oa_url       = COALESCE(EXCLUDED.oa_url,   papers.oa_url),
                        open_access  = EXCLUDED.open_access
                RETURNING id
                """
            ),
            {
                "id": paper_id,
                "doi": doi,
                "title": paper.title,
                "abstract": paper.abstract,
                "year": paper.year,
                "venue": paper.venue,
                "volume": paper.volume,
                "issue": paper.issue,
                "oa": paper.open_access,
                "oa_url": paper.oa_url,
                "has_abs": paper.has_abstract,
                "has_refs": paper.has_references,
            },
        )

        row = await db.execute(
            text(
                "SELECT id FROM papers WHERE doi = :doi"
                if doi
                else "SELECT id FROM papers WHERE id = :id"
            ),
            {"doi": doi} if doi else {"id": paper_id},
        )
        actual_id = str(row.scalar() or paper_id)

        # Source
        await db.execute(
            text(
                """
                INSERT INTO paper_sources (paper_id, provider, provider_id, raw_metadata)
                VALUES (:pid, :prov, :pvid, :raw)
                ON CONFLICT (provider, provider_id) DO NOTHING
                """
            ),
            {
                "pid": actual_id,
                "prov": paper.source_provider,
                "pvid": paper.provider_id,
                "raw": json.dumps(paper.raw_metadata),
            },
        )

        # Authors
        for author in paper.authors:
            aid = str(uuid.uuid4())
            await db.execute(
                text(
                    """
                    INSERT INTO authors (id, name, family_name, orcid)
                    VALUES (:id, :name, :family, :orcid)
                    ON CONFLICT (orcid) WHERE orcid IS NOT NULL DO NOTHING
                    """
                ),
                {
                    "id": aid,
                    "name": author.name,
                    "family": author.family_name,
                    "orcid": author.orcid,
                },
            )
            arow = await db.execute(
                text(
                    "SELECT id FROM authors WHERE orcid = :orcid"
                    if author.orcid
                    else "SELECT id FROM authors WHERE id = :id"
                ),
                {"orcid": author.orcid} if author.orcid else {"id": aid},
            )
            actual_aid = str(arow.scalar() or aid)
            await db.execute(
                text(
                    "INSERT INTO paper_authors (paper_id, author_id, position) VALUES (:pid, :aid, :pos) ON CONFLICT DO NOTHING"
                ),
                {"pid": actual_id, "aid": actual_aid, "pos": author.position},
            )

        # Topics
        for topic in paper.topics[:5]:
            await db.execute(
                text(
                    "INSERT INTO paper_topics (paper_id, topic, source) VALUES (:pid, :topic, :src) ON CONFLICT DO NOTHING"
                ),
                {"pid": actual_id, "topic": topic, "src": paper.source_provider},
            )

        # Queue for indexing
        await db.execute(
            text(
                "INSERT INTO qdrant_indexing_queue (entity_type, entity_id, operation) VALUES ('paper', :eid, 'upsert')"
            ),
            {"eid": actual_id},
        )

        await db.commit()
        logger.info("live_fetched_paper_stored", paper_id=actual_id, doi=doi, title=paper.title)
        return actual_id
    except Exception as exc:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.warning("persist_paper_db_failed_fallback_uuid", title=paper.title, error=str(exc))
        # Stable deterministic UUID fallback from DOI or title
        seed_str = doi or paper.provider_id or paper.title
        return str(uuid.uuid5(uuid.NAMESPACE_URL, seed_str))


async def fetch_and_store_by_id(db: AsyncSession, paper_id: str) -> dict[str, Any] | None:
    """
    Given a DOI or arXiv ID string, fetch from the appropriate provider,
    persist to DB (or generate fallback ID if DB unavailable), and return paper dict.
    """
    value = paper_id.strip()
    if value.lower().startswith("doi:"):
        value = value[4:].strip()

    normalized_paper: NormalizedPaper | None = None

    if _looks_like_arxiv_id(value):
        clean_aid = value[6:] if value.lower().startswith("arxiv:") else value
        normalized_paper = await ArXivAdapter().get_by_id(clean_aid)

    if normalized_paper is None and _looks_like_doi(value):
        normalized_paper = await OpenAlexAdapter().get_by_doi(value)

    if normalized_paper is None:
        results = await OpenAlexAdapter().search(value, limit=1)
        if _looks_like_doi(value):
            requested = normalize_doi(value)
            for result in results:
                if result.doi and normalize_doi(result.doi) == requested:
                    normalized_paper = result
                    break
        elif results:
            normalized_paper = results[0]

    if normalized_paper is None:
        return None

    stored_id = await _persist(db, normalized_paper)

    return {
        "id": stored_id,
        "doi": normalize_doi(normalized_paper.doi),
        "title": normalized_paper.title,
        "abstract": normalized_paper.abstract,
        "year": normalized_paper.year,
        "venue": normalized_paper.venue,
        "volume": normalized_paper.volume,
        "issue": normalized_paper.issue,
        "open_access": normalized_paper.open_access,
        "oa_url": normalized_paper.oa_url,
        "has_abstract": normalized_paper.has_abstract,
        "has_references": normalized_paper.has_references,
        "authors": [
            {"name": a.name, "family_name": a.family_name, "orcid": a.orcid, "position": a.position}
            for a in normalized_paper.authors
        ],
        "topics": normalized_paper.topics[:5],
        "source_providers": [normalized_paper.source_provider],
    }


async def live_search_and_store(
    db: AsyncSession, query: str, limit: int = 20
) -> list[dict[str, Any]]:
    """
    Live-search OpenAlex + arXiv concurrently, persist results to DB (if online),
    and return list of paper dicts. Never fails empty on DB errors.
    """
    import asyncio

    oa_results, arxiv_results = await asyncio.gather(
        OpenAlexAdapter().search(query, limit=limit),
        ArXivAdapter().search(query, limit=limit),
        return_exceptions=True,
    )

    papers: list[NormalizedPaper] = []
    if isinstance(oa_results, list):
        papers.extend(oa_results)
    if isinstance(arxiv_results, list):
        papers.extend(arxiv_results)

    seen_keys: set[str] = set()
    out: list[dict[str, Any]] = []

    for paper in papers:
        key = normalize_doi(paper.doi) or paper.provider_id or paper.title.lower()
        if key in seen_keys:
            continue
        seen_keys.add(key)

        stored_id = await _persist(db, paper)
        out.append(
            {
                "id": stored_id,
                "doi": normalize_doi(paper.doi),
                "title": paper.title,
                "abstract": paper.abstract or "",
                "year": paper.year,
                "venue": paper.venue,
                "open_access": paper.open_access,
                "oa_url": paper.oa_url,
                "authors": [{"name": a.name, "position": a.position} for a in paper.authors],
                "topics": paper.topics[:5],
                "source_providers": [paper.source_provider],
                "score": 0.5,
                "explanation": {"matched_terms": [], "details": ["live fetch"]},
            }
        )
        if len(out) >= limit:
            break

    return out
