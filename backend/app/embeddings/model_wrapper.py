from __future__ import annotations

import hashlib
import math


def hash_embed(text: str, dimensions: int = 768) -> list[float]:
    """Deterministic bag-of-tokens embedding. Used when EMBEDDING_BACKEND=hash."""
    vector = [0.0] * dimensions
    tokens = text.lower().split()
    if not tokens:
        return vector
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def embed_texts(
    texts: list[str], *, backend: str = "hash", dimensions: int = 768
) -> list[list[float]]:
    if backend == "fastembed":
        return _fastembed(texts)
    if backend != "hash":
        raise ValueError(f"Unknown embedding backend {backend}")
    return [hash_embed(text, dimensions) for text in texts]


def _fastembed(texts: list[str]) -> list[list[float]]:
    from fastembed import TextEmbedding

    model = TextEmbedding(model_name="BAAI/bge-base-en-v1.5")
    return [vector.tolist() for vector in model.embed(texts)]
