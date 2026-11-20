from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.claim_extractor import extract_citations
from app.rag.llm_provider import Message, get_llm_provider
from app.reviews.projects import get_review_papers

SECTION_TYPES = [
    "overview",
    "themes",
    "methodologies",
    "findings",
    "similarities",
    "contradictions",
    "limitations",
    "gaps",
    "future_directions",
]

SECTION_PROMPTS = {
    "overview": "Synthesize a structured research overview summarizing the scope and primary questions across these papers.",
    "themes": "Identify and discuss the central theoretical and empirical themes uniting these studies.",
    "methodologies": "Compare the technical and empirical methodologies used in these works.",
    "findings": "Detail the key experimental findings, benchmark outcomes, and verified results.",
    "similarities": "Analyze areas of consensus and common findings between the authors.",
    "contradictions": "Highlight divergences, disagreements, or conflicting outcomes in the literature.",
    "limitations": "Identify explicit constraints and empirical limitations reported in the sources.",
    "gaps": "Outline unresolved research questions and blind spots in the current body of work.",
    "future_directions": "Propose strategic future research trajectories suggested by the findings.",
}


async def generate_section(
    review_id: uuid.UUID,
    section_type: str,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> dict[str, Any]:
    if section_type not in SECTION_TYPES:
        raise ValueError(f"Unknown section type {section_type}")

    papers = await get_review_papers(db, review_id, user_id)
    if not papers:
        raise ValueError("Cannot synthesize a review without any papers in the project")

    # Check if full chunks exist
    pids = [str(p["id"]) for p in papers]
    chunk_rows = await db.execute(
        text("SELECT id, paper_id, text FROM document_chunks WHERE paper_id = ANY(:pids) LIMIT 50"),
        {"pids": pids},
    )
    chunks = [dict(r) for r in chunk_rows.mappings()]

    is_abstract_only = len(chunks) == 0

    if is_abstract_only:
        context_body = "\n\n".join(
            [f"Paper: {p['title']} ({p.get('year')})\nAbstract: {p.get('abstract') or 'No abstract'}" for p in papers]
        )
    else:
        context_body = "\n\n".join([f"[CITATION:{c['id']}]\n{c['text']}\n[/CITATION]" for c in chunks])

    prompt = SECTION_PROMPTS.get(section_type, "Synthesize this section.")
    provider = get_llm_provider()

    messages = [
        Message(
            role="system",
            content="You are a research synthesis engine. Write structured, academic prose. Ground every claim.",
        ),
        Message(
            role="user",
            content=f"{prompt}\n\nEvidence Context:\n{context_body}",
        ),
    ]

    llm_resp = await provider.complete(messages, temperature=0.0)
    sec_id = str(uuid.uuid4())

    await db.execute(
        text(
            """
            INSERT INTO synthesis_sections (id, review_id, section_type, content, is_abstract_only, generated_at, model_id)
            VALUES (:id, :rid, :type, :content, :abs, now(), :model)
            ON CONFLICT (review_id, section_type)
            DO UPDATE SET content = EXCLUDED.content, generated_at = now(), model_id = EXCLUDED.model_id
            """
        ),
        {
            "id": sec_id,
            "rid": str(review_id),
            "type": section_type,
            "content": llm_resp.content,
            "abs": is_abstract_only,
            "model": llm_resp.model_id,
        },
    )
    await db.commit()

    return {
        "id": sec_id,
        "review_id": review_id,
        "section_type": section_type,
        "content": llm_resp.content,
        "is_abstract_only": is_abstract_only,
        "model_id": llm_resp.model_id,
    }
