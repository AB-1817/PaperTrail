from __future__ import annotations

import hashlib
import math

import structlog

logger = structlog.get_logger(__name__)

_fastembed_model = None
_fastembed_failed = False


def hash_embed(text: str, dimensions: int = 768) -> list[float]:
    vector = [0.0] * dimensions
    tokens = text.lower().split()
    if not tokens:
        return vector
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


def _get_fastembed_model():
    global _fastembed_model, _fastembed_failed
    if _fastembed_model is not None:
        return _fastembed_model
    if _fastembed_failed:
        return None
    try:
        from fastembed import TextEmbedding
        _fastembed_model = TextEmbedding(model_name="BAAI/bge-base-en-v1.5")
        logger.info("fastembed_model_loaded", model="BAAI/bge-base-en-v1.5")
        return _fastembed_model
    except Exception as exc:
        _fastembed_failed = True
        logger.warning("fastembed_load_failed_using_hash", error=str(exc))
        return None


def embed_texts(
    texts: list[str], *, backend: str = "hash", dimensions: int = 768
) -> list[list[float]]:
    if backend == "fastembed":
        model = _get_fastembed_model()
        if model is not None:
            try:
                return [v.tolist() for v in model.embed(texts)]
            except Exception as exc:
                logger.warning("fastembed_embed_failed_falling_back", error=str(exc))
        # fall through to hash
    elif backend != "hash":
        raise ValueError(f"Unknown embedding backend {backend}")
    return [hash_embed(text, dimensions) for text in texts]
