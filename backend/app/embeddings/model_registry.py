from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EmbeddingModelConfig:
    model_name: str
    model_version: str
    dimensions: int
    distance: str
    bm25_model: str
    bm25_version: str


def get_active_config() -> EmbeddingModelConfig:
    from app.core.config import get_settings

    s = get_settings()
    return EmbeddingModelConfig(
        model_name=s.embedding_model,
        model_version=s.embedding_model_version,
        dimensions=768,
        distance="cosine",
        bm25_model=s.bm25_model,
        bm25_version="1.0",
    )
