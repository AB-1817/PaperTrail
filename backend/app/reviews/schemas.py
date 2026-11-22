from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class ReviewResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: str | None = None
    status: str
    paper_count: int = 0
    created_at: datetime
    updated_at: datetime


class SectionResponse(BaseModel):
    id: uuid.UUID
    review_id: uuid.UUID
    section_type: str
    content: str | None = None
    is_abstract_only: bool = False
    generated_at: datetime | None = None
    model_id: str | None = None


class ReviewAddPaper(BaseModel):
    paper_id: uuid.UUID
