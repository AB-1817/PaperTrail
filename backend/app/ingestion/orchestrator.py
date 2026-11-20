from __future__ import annotations

import json
import uuid
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.deduplicator import ExistingPaper, find_duplicate
from app.ingestion.job_tracker import final_status
from app.ingestion.normalizer import normalize_doi, normalize_title
from app.providers.arxiv import ArXivAdapter
from app.providers.crossref import CrossrefAdapter
from app.providers.openalex import OpenAlexAdapter
from app.providers.semantic_scholar import SemanticScholarAdapter

logger = structlog.get_logger(__name__)


def get_adapter(provider_name: str) -> Any:
    adapters = {
        "openalex": OpenAlexAdapter,
        "arxiv": ArXivAdapter,
        "semantic_scholar": SemanticScholarAdapter,
        "crossref": CrossrefAdapter,
    }
    adapter_cls = adapters.get(provider_name.lower())
    if not adapter_cls:
        raise ValueError(f"Unknown provider '{provider_name}'. Available: {list(adapters.keys())}")
    return adapter_cls()


async def run_ingestion(
    job_id: str,
    provider_name: str,
    query: str,
    limit: int,
    db: AsyncSession,
) -> None:
    logger.info("ingestion_started", job_id=job_id, provider=provider_name, query=query)

    # Set status to running
    await db.execute(
        text("UPDATE ingestion_jobs SET status = 'running', started_at = now() WHERE id = :jid"),
        {"jid": job_id},
    )
    await db.commit()

    adapter = get_adapter(provider_name)
    errors: list[str] = []
    inserted_count = 0
    updated_count = 0

    try:
        papers = await adapter.search(query, limit=limit)
    except Exception as exc:
        logger.error("provider_search_failed", provider=provider_name, error=str(exc))
        errors.append(f"Provider search failed: {exc}")
        await db.execute(
            text(
                "UPDATE ingestion_jobs SET status = 'failed', errors = :errors, completed_at = now() WHERE id = :jid"
            ),
            {"jid": job_id, "errors": json.dumps(errors)},
        )
        await db.commit()
        return

    # Load existing papers for in-memory deduplication
    rows = await db.execute(text("SELECT id, doi, title, year FROM papers LIMIT 5000"))
    existing: list[ExistingPaper] = []
    for r in rows.mappings():
        existing.append(
            ExistingPaper(
                id=str(r["id"]),
                doi=r["doi"],
                title_norm=normalize_title(r["title"]),
                year=r["year"],
                first_author_family=None,
            )
        )

    for paper in papers:
        try:
            match = find_duplicate(paper, existing)
            if match is not None:
                # Existing paper - add source link
                paper_id = match.paper_id
                await db.execute(
                    text(
                        """
                        INSERT INTO paper_sources (paper_id, provider, provider_id, raw_metadata)
                        VALUES (:pid, :prov, :pvid, :raw)
                        ON CONFLICT (provider, provider_id) DO NOTHING
                        """
                    ),
                    {
                        "pid": paper_id,
                        "prov": paper.source_provider,
                        "pvid": paper.provider_id,
                        "raw": json.dumps(paper.raw_metadata),
                    },
                )
                updated_count += 1
            else:
                # New paper
                paper_id = str(uuid.uuid4())
                await db.execute(
                    text(
                        """
                        INSERT INTO papers (id, doi, title, abstract, year, venue, volume, issue, open_access, oa_url, has_abstract, has_references)
                        VALUES (:id, :doi, :title, :abstract, :year, :venue, :volume, :issue, :oa, :oa_url, :has_abs, :has_refs)
                        ON CONFLICT (doi) DO NOTHING
                        """
                    ),
                    {
                        "id": paper_id,
                        "doi": normalize_doi(paper.doi),
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

                # Insert source
                await db.execute(
                    text(
                        """
                        INSERT INTO paper_sources (paper_id, provider, provider_id, raw_metadata)
                        VALUES (:pid, :prov, :pvid, :raw)
                        ON CONFLICT (provider, provider_id) DO NOTHING
                        """
                    ),
                    {
                        "pid": paper_id,
                        "prov": paper.source_provider,
                        "pvid": paper.provider_id,
                        "raw": json.dumps(paper.raw_metadata),
                    },
                )

                # Authors
                for author in paper.authors:
                    author_id = str(uuid.uuid4())
                    await db.execute(
                        text(
                            """
                            INSERT INTO authors (id, name, family_name, orcid)
                            VALUES (:id, :name, :family, :orcid)
                            ON CONFLICT (orcid) WHERE orcid IS NOT NULL DO NOTHING
                            """
                        ),
                        {
                            "id": author_id,
                            "name": author.name,
                            "family": author.family_name,
                            "orcid": author.orcid,
                        },
                    )

                    await db.execute(
                        text(
                            """
                            INSERT INTO paper_authors (paper_id, author_id, position)
                            VALUES (:pid, :aid, :pos)
                            ON CONFLICT DO NOTHING
                            """
                        ),
                        {"pid": paper_id, "aid": author_id, "pos": author.position},
                    )

                # Topics
                for topic in paper.topics[:5]:
                    await db.execute(
                        text(
                            """
                            INSERT INTO paper_topics (paper_id, topic, source)
                            VALUES (:pid, :topic, :source)
                            ON CONFLICT DO NOTHING
                            """
                        ),
                        {"pid": paper_id, "topic": topic, "source": paper.source_provider},
                    )

                # Enqueue into Qdrant indexing queue
                await db.execute(
                    text(
                        """
                        INSERT INTO qdrant_indexing_queue (entity_type, entity_id, operation)
                        VALUES ('paper', :eid, 'upsert')
                        """
                    ),
                    {"eid": paper_id},
                )

                existing.append(
                    ExistingPaper(
                        id=paper_id,
                        doi=paper.doi,
                        title_norm=normalize_title(paper.title),
                        year=paper.year,
                        first_author_family=paper.authors[0].family_name if paper.authors else None,
                    )
                )
                inserted_count += 1

            await db.commit()

        except Exception as exc:
            await db.rollback()
            logger.warning("paper_ingestion_failed", title=paper.title, error=str(exc))
            errors.append(f"{paper.title}: {exc}")

    status = final_status(
        papers_inserted=inserted_count,
        papers_updated=updated_count,
        errors=errors,
    )

    await db.execute(
        text(
            """
            UPDATE ingestion_jobs
            SET status = :status,
                papers_found = :found,
                papers_inserted = :inserted,
                papers_updated = :updated,
                errors = :errors,
                completed_at = now()
            WHERE id = :jid
            """
        ),
        {
            "status": status,
            "found": len(papers),
            "inserted": inserted_count,
            "updated": updated_count,
            "errors": json.dumps(errors),
            "jid": job_id,
        },
    )
    await db.commit()
    logger.info("ingestion_completed", job_id=job_id, status=status, inserted=inserted_count)
