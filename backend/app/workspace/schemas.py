from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CollectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class CollectionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class CollectionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime
    paper_count: int = 0


class CollectionAddPaper(BaseModel):
    paper_id: uuid.UUID


class SavedPaperResponse(BaseModel):
    id: uuid.UUID
    paper_id: uuid.UUID
    saved_at: datetime
    paper_title: str | None = None
    paper_year: int | None = None


class NoteCreate(BaseModel):
    paper_id: uuid.UUID
    content: str = Field(..., min_length=1)


class NoteUpdate(BaseModel):
    content: str = Field(..., min_length=1)


class NoteResponse(BaseModel):
    id: uuid.UUID
    paper_id: uuid.UUID
    content: str
    created_at: datetime
    updated_at: datetime


class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)


class TagResponse(BaseModel):
    id: uuid.UUID
    name: str


class ReadingProgressUpdate(BaseModel):
    status: str = Field(..., pattern="^(to_read|reading|read|archived)$")


class ReadingProgressResponse(BaseModel):
    paper_id: uuid.UUID
    status: str
    updated_at: datetime
