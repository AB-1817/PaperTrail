from __future__ import annotations

import uuid

from pydantic import BaseModel


class ExplanationDetail(BaseModel):
    primary_reason: str
    details: list[str]
    component_scores: dict[str, float]


class RecommendationItem(BaseModel):
    paper_id: uuid.UUID
    title: str
    year: int | None = None
    venue: str | None = None
    open_access: bool = False
    score: float
    explanation: ExplanationDetail


class EventCreate(BaseModel):
    paper_id: uuid.UUID
    event_type: str
    source: str | None = None
