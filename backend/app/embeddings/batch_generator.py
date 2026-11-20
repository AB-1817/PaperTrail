from __future__ import annotations

from app.core.config import get_settings
from app.embeddings.model_wrapper import embed_texts


def embed_batch(texts: list[str]) -> list[list[float]]:
    settings = get_settings()
    return embed_texts(texts, backend=settings.embedding_backend, dimensions=768)


def embed_single(text: str) -> list[float]:
    return embed_batch([text])[0]
