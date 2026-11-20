from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import UserContext, get_current_user
from app.core.db import get_db
from app.workspace import service
from app.workspace.schemas import (
    CollectionAddPaper,
    CollectionCreate,
    CollectionResponse,
    CollectionUpdate,
    NoteCreate,
    NoteResponse,
    ReadingProgressUpdate,
)

router = APIRouter(prefix="/workspace", tags=["workspace"])
collections_router = APIRouter(prefix="/collections", tags=["collections"])

# ── Collections ─────────────────────────────────────────────────────────────


@collections_router.get("", response_model=dict[str, Any])
async def list_collections(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await service.list_collections(db, current_user, page, per_page)


@collections_router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    body: CollectionCreate,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CollectionResponse:
    return await service.create_collection(db, current_user, body)


@collections_router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(
    collection_id: uuid.UUID,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CollectionResponse:
    return await service.get_collection(db, collection_id, current_user)


@collections_router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: uuid.UUID,
    body: CollectionUpdate,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CollectionResponse:
    return await service.update_collection(db, collection_id, current_user, body)


@collections_router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_collection(
    collection_id: uuid.UUID,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    await service.delete_collection(db, collection_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@collections_router.post("/{collection_id}/papers", status_code=status.HTTP_200_OK)
async def add_paper_to_collection(
    collection_id: uuid.UUID,
    body: CollectionAddPaper,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    from app.workspace import repository

    ok = await repository.add_paper_to_collection(db, collection_id, current_user.user_id, body.paper_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Collection not found")
    return {"status": "added"}


@collections_router.delete("/{collection_id}/papers/{paper_id}", status_code=status.HTTP_200_OK)
async def remove_paper_from_collection(
    collection_id: uuid.UUID,
    paper_id: uuid.UUID,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    from app.workspace import repository

    ok = await repository.remove_paper_from_collection(db, collection_id, current_user.user_id, paper_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Paper not found in collection")
    return {"status": "removed"}


# ── Saved Papers ────────────────────────────────────────────────────────────


@router.get("/saved-papers")
async def list_saved_papers(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await service.list_saved_papers(db, current_user, page, per_page)


@router.post("/saved-papers", status_code=status.HTTP_201_CREATED)
async def save_paper(
    body: CollectionAddPaper,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await service.save_paper(db, current_user, body.paper_id)


@router.delete("/saved-papers/{paper_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def unsave_paper(
    paper_id: uuid.UUID,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    await service.unsave_paper(db, current_user, paper_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Notes ───────────────────────────────────────────────────────────────────


@router.get("/notes")
async def list_notes(
    paper_id: uuid.UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await service.list_notes(db, current_user, paper_id, page, per_page)


@router.post("/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    body: NoteCreate,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NoteResponse:
    return await service.create_note(db, current_user, body)


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_note(
    note_id: uuid.UUID,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    await service.delete_note(db, note_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Reading Progress ────────────────────────────────────────────────────────


@router.put("/reading-progress/{paper_id}")
async def set_reading_progress(
    paper_id: uuid.UUID,
    body: ReadingProgressUpdate,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await service.set_reading_progress(db, current_user, paper_id, body)
