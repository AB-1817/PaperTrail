from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import UserContext, get_current_user
from app.core.db import get_db
from app.evaluation import benchmark_manager, experiment_runner

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


class DatasetCreateRequest(BaseModel):
    name: str
    version: str
    description: str | None = None
    domain: str = "ai_cs"


class JudgmentCreateRequest(BaseModel):
    query: str
    paper_id: uuid.UUID
    relevance: int = Field(..., ge=0, le=2)
    annotator: str
    source: str = "manual_evaluation"


class ExperimentCreateRequest(BaseModel):
    name: str
    strategy: str = Field(..., pattern="^(bm25_only|dense_only|hybrid_rrf|hybrid_rerank)$")
    dataset_id: uuid.UUID | None = None
    config: dict[str, Any] = {}


@router.get("/datasets")
async def list_datasets(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    rows = await db.execute(text("SELECT * FROM evaluation_datasets ORDER BY created_at DESC"))
    items = [dict(r) for r in rows.mappings()]
    return {"data": items, "meta": {"total": len(items)}, "error": None}


@router.post("/datasets", status_code=status.HTTP_201_CREATED)
async def create_dataset(
    body: DatasetCreateRequest,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    dataset_id = await benchmark_manager.get_or_create_dataset(
        db,
        name=body.name,
        version=body.version,
        description=body.description,
        domain=body.domain,
    )
    return {"data": {"id": dataset_id}, "meta": None, "error": None}


@router.post("/datasets/{dataset_id}/judgments", status_code=status.HTTP_201_CREATED)
async def add_judgment(
    dataset_id: uuid.UUID,
    body: JudgmentCreateRequest,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    await benchmark_manager.add_judgment(
        db,
        dataset_id=str(dataset_id),
        query=body.query,
        paper_id=str(body.paper_id),
        relevance=body.relevance,
        annotator=body.annotator,
        source=body.source,
    )
    return {"data": {"status": "created"}, "meta": None, "error": None}


@router.get("/datasets/{dataset_id}/judgments")
async def get_judgments(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    judgments = await benchmark_manager.get_judgments(db, str(dataset_id))
    return {"data": judgments, "meta": {"total": len(judgments)}, "error": None}


@router.get("/experiments")
async def list_experiments(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    rows = await db.execute(text("SELECT * FROM retrieval_experiments ORDER BY created_at DESC"))
    items = [dict(r) for r in rows.mappings()]
    return {"data": items, "meta": {"total": len(items)}, "error": None}


@router.post("/experiments", status_code=status.HTTP_201_CREATED)
async def create_experiment(
    body: ExperimentCreateRequest,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    exp_id = await experiment_runner.create_experiment(
        db,
        name=body.name,
        strategy=body.strategy,
        config=body.config,
        dataset_id=str(body.dataset_id) if body.dataset_id else None,
    )
    return {"data": {"id": exp_id, "status": "pending"}, "meta": None, "error": None}


@router.post("/experiments/{experiment_id}/run", status_code=status.HTTP_202_ACCEPTED)
async def run_experiment_endpoint(
    experiment_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    background_tasks.add_task(experiment_runner.run_experiment, str(experiment_id), db)
    return {"data": {"id": str(experiment_id), "status": "running"}, "meta": None, "error": None}


@router.get("/experiments/{experiment_id}/results")
async def get_experiment_results(
    experiment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    rows = await db.execute(
        text("SELECT metric, value, k, computed_at FROM evaluation_results WHERE experiment_id = :id"),
        {"id": str(experiment_id)},
    )
    items = [dict(r) for r in rows.mappings()]
    return {"data": items, "meta": {"total": len(items)}, "error": None}
