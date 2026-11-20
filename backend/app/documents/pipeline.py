from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.chunker import chunk_document
from app.documents.fetcher import download_pdf
from app.documents.grobid_parser import GROBIDParser
from app.documents.pypdf_parser import PyPDFParser
from app.outbox.indexing_queue import enqueue

logger = structlog.get_logger(__name__)


async def process_document(
    document_id: uuid.UUID,
    paper_id: uuid.UUID,
    pdf_url: str,
    access_type: str,
    db: AsyncSession,
) -> None:
    logger.info("document_processing_started", doc_id=str(document_id), url=pdf_url)

    await db.execute(
        text("UPDATE documents SET parse_status = 'processing' WHERE id = :id"),
        {"id": str(document_id)},
    )
    await db.commit()

    try:
        content_bytes, sha256 = await download_pdf(pdf_url)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(content_bytes)
            tmp_path = Path(tmp.name)

        # Parse with GROBID fallback to PyPDF
        parsed_doc = None
        parser_used = "grobid"
        try:
            grobid = GROBIDParser()
            parsed_doc = grobid.parse(tmp_path)
        except Exception:
            parser_used = "pypdf"
            pypdf_p = PyPDFParser()
            parsed_doc = pypdf_p.parse(tmp_path)

        tmp_path.unlink(missing_ok=True)

        chunks = chunk_document(parsed_doc)

        for chunk in chunks:
            chunk_id = str(uuid.uuid4())
            await db.execute(
                text(
                    """
                    INSERT INTO document_chunks (
                        id, document_id, paper_id, chunk_index,
                        text, page_number, char_offset, section, token_count
                    )
                    VALUES (
                        :id, :doc_id, :pid, :idx,
                        :text, :page, :offset, :sec, :tokens
                    )
                    """
                ),
                {
                    "id": chunk_id,
                    "doc_id": str(document_id),
                    "pid": str(paper_id),
                    "idx": chunk["chunk_index"],
                    "text": chunk["text"],
                    "page": chunk["page_number"],
                    "offset": chunk["char_offset"],
                    "sec": chunk["section"],
                    "tokens": chunk["token_count"],
                },
            )
            # Enqueue to Qdrant
            await enqueue(db, entity_type="chunk", entity_id=chunk_id)

        await db.execute(
            text(
                """
                UPDATE documents
                SET parse_status = 'complete',
                    parser_used = :parser,
                    page_count = :pages,
                    file_checksum = :sha,
                    parsed_at = now()
                WHERE id = :id
                """
            ),
            {
                "id": str(document_id),
                "parser": parser_used,
                "pages": parsed_doc.page_count,
                "sha": sha256,
            },
        )
        await db.commit()
        logger.info("document_processing_complete", doc_id=str(document_id), chunks=len(chunks))

    except Exception as exc:
        logger.error("document_processing_failed", doc_id=str(document_id), error=str(exc))
        await db.execute(
            text("UPDATE documents SET parse_status = 'failed' WHERE id = :id"),
            {"id": str(document_id)},
        )
        await db.commit()
