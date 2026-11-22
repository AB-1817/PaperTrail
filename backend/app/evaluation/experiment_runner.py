from __future__ import annotations

import json
import uuid
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.embeddings.batch_generator import embed_batch
from app.evaluation.metrics import compute_all_metrics
from app.search.ranking import rank_papers
from app.search.reranker import lexical_rerank
from app.search.types import PaperDoc

logger = structlog.get_logger(__name__)


async def create_experiment(
    db: AsyncSession,
    name: str,
    strategy: str,
    config: dict[str, Any],
    dataset_id: str | None = None,
) -> str:
    settings = get_settings()
    exp_id = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO retrieval_experiments (
                id, name, strategy, config, dataset_id,
                embedding_model, reranker_model, status
            )
            VALUES (:id, :name, :strategy, :config, :did, :emb, :rerank, 'pending')
            """
        ),
        {
            "id": exp_id,
            "name": name,
            "strategy": strategy,
            "config": json.dumps(config),
            "did": dataset_id,
            "emb": settings.embedding_model,
            "rerank": settings.reranker_model,
        },
    )
    await db.commit()
    return exp_id


async def run_experiment(experiment_id: str, db: AsyncSession) -> dict[str, Any]:
    logger.info("evaluation_experiment_started", experiment_id=experiment_id)

    # Update to running
    await db.execute(
        text("UPDATE retrieval_experiments SET status = 'running' WHERE id = :id"),
        {"id": experiment_id},
    )
    await db.commit()

    # Load experiment
    exp_row = await db.execute(
        text("SELECT * FROM retrieval_experiments WHERE id = :id"),
        {"id": experiment_id},
    )
    exp = exp_row.mappings().first()
    if not exp:
        raise ValueError(f"Experiment {experiment_id} not found")

    dataset_id = str(exp["dataset_id"]) if exp["dataset_id"] else None
    strategy = exp["strategy"]

    # Fetch paper pool
    paper_rows = await db.execute(
        text("SELECT id, title, abstract, year, venue, open_access, doi FROM papers LIMIT 500")
    )
    papers = [
        PaperDoc(
            id=str(r["id"]),
            title=r["title"],
            abstract=r["abstract"],
            year=r["year"],
            venue=r["venue"],
            open_access=r["open_access"],
            doi=r["doi"],
        )
        for r in paper_rows.mappings()
    ]

    # Fetch judgments
    judgments_query = "SELECT query, paper_id, relevance FROM relevance_judgments"
    params = {}
    if dataset_id:
        judgments_query += " WHERE dataset_id = :did"
        params["did"] = dataset_id

    j_rows = await db.execute(text(judgments_query), params)
    query_judgments: dict[str, dict[str, int]] = {}
    for r in j_rows.mappings():
        q = r["query"]
        if q not in query_judgments:
            query_judgments[q] = {}
        query_judgments[q][str(r["paper_id"])] = r["relevance"]

    if not query_judgments:
        # No judgments found, mark complete with zero results
        await db.execute(
            text(
                "UPDATE retrieval_experiments SET status = 'complete', completed_at = now() WHERE id = :id"
            ),
            {"id": experiment_id},
        )
        await db.commit()
        return {"status": "complete", "queries_evaluated": 0}

    # Evaluate each query
    metric_accumulators: dict[str, list[float]] = {}
    for query, graded_rel in query_judgments.items():
        ranked = rank_papers(
            strategy=strategy,
            query=query,
            papers=papers,
            embedder=embed_batch,
            reranker=lexical_rerank,
        )
        ranked_ids = [item.paper.id for item in ranked]
        metrics = compute_all_metrics(ranked_ids, graded_rel)

        for m_name, val in metrics.items():
            if m_name not in metric_accumulators:
                metric_accumulators[m_name] = []
            metric_accumulators[m_name].append(val)

    # Average metrics and record in evaluation_results
    for metric_name, values in metric_accumulators.items():
        avg_value = sum(values) / len(values) if values else 0.0
        k_val = int(metric_name.split("@")[-1]) if "@" in metric_name else None

        await db.execute(
            text(
                """
                INSERT INTO evaluation_results (id, experiment_id, metric, value, k)
                VALUES (:id, :eid, :metric, :val, :k)
                ON CONFLICT (experiment_id, metric, k)
                DO UPDATE SET value = EXCLUDED.value, computed_at = now()
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "eid": experiment_id,
                "metric": metric_name,
                "val": round(avg_value, 4),
                "k": k_val,
            },
        )

    await db.execute(
        text(
            "UPDATE retrieval_experiments SET status = 'complete', completed_at = now() WHERE id = :id"
        ),
        {"id": experiment_id},
    )
    await db.commit()
    logger.info("evaluation_experiment_completed", experiment_id=experiment_id)
    return {"status": "complete", "queries_evaluated": len(query_judgments)}
