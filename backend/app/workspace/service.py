from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import UserContext
from app.workspace import repository
from app.workspace.schemas import (
    CollectionCreate,
    CollectionResponse,
    CollectionUpdate,
    NoteCreate,
    NoteResponse,
    NoteUpdate,
    ReadingProgressResponse,
    ReadingProgressUpdate,
    SavedPaperResponse,
)


async def create_collection(
    db: AsyncSession, user: UserContext, body: CollectionCreate
) -> CollectionResponse:
    item = await repository.create_collection(db, user.user_id, body.name, body.description)
    return CollectionResponse(**item)


async def get_collection(
    db: AsyncSession, collection_id: uuid.UUID, user: UserContext
) -> CollectionResponse:
    item = await repository.get_collection(db, collection_id, user.user_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    return CollectionResponse(**item)


async def list_collections(
    db: AsyncSession, user: UserContext, page: int, per_page: int
) -> dict[str, Any]:
    items, total = await repository.list_collections(db, user.user_id, page, per_page)
    return {
        "data": [CollectionResponse(**i) for i in items],
        "meta": {"page": page, "per_page": per_page, "total": total},
        "error": None,
    }


async def update_collection(
    db: AsyncSession, collection_id: uuid.UUID, user: UserContext, body: CollectionUpdate
) -> CollectionResponse:
    item = await repository.update_collection(
        db, collection_id, user.user_id, name=body.name, description=body.description
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    return CollectionResponse(**item)


async def delete_collection(
    db: AsyncSession, collection_id: uuid.UUID, user: UserContext
) -> None:
    deleted = await repository.delete_collection(db, collection_id, user.user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")


async def save_paper(
    db: AsyncSession, user: UserContext, paper_id: uuid.UUID
) -> dict[str, Any]:
    return await repository.save_paper(db, user.user_id, paper_id)


async def unsave_paper(
    db: AsyncSession, user: UserContext, paper_id: uuid.UUID
) -> None:
    deleted = await repository.unsave_paper(db, user.user_id, paper_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved paper not found")


async def list_saved_papers(
    db: AsyncSession, user: UserContext, page: int, per_page: int
) -> dict[str, Any]:
    items, total = await repository.list_saved_papers(db, user.user_id, page, per_page)
    return {
        "data": [SavedPaperResponse(**i) for i in items],
        "meta": {"page": page, "per_page": per_page, "total": total},
        "error": None,
    }


async def create_note(
    db: AsyncSession, user: UserContext, body: NoteCreate
) -> NoteResponse:
    item = await repository.create_note(db, user.user_id, body.paper_id, body.content)
    return NoteResponse(**item)


async def list_notes(
    db: AsyncSession, user: UserContext, paper_id: uuid.UUID | None, page: int, per_page: int
) -> dict[str, Any]:
    items, total = await repository.list_notes(db, user.user_id, paper_id, page, per_page)
    return {
        "data": [NoteResponse(**i) for i in items],
        "meta": {"page": page, "per_page": per_page, "total": total},
        "error": None,
    }


async def delete_note(db: AsyncSession, note_id: uuid.UUID, user: UserContext) -> None:
    deleted = await repository.delete_note(db, note_id, user.user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")


async def set_reading_progress(
    db: AsyncSession, user: UserContext, paper_id: uuid.UUID, body: ReadingProgressUpdate
) -> dict[str, Any]:
    return await repository.upsert_reading_progress(db, user.user_id, paper_id, body.status)
