from __future__ import annotations

import structlog

from app.search.bm25 import tokenize

logger = structlog.get_logger(__name__)

_cross_encoder = None
_cross_encoder_failed = False


def _get_cross_encoder():
    global _cross_encoder, _cross_encoder_failed
    if _cross_encoder is not None:
        return _cross_encoder
    if _cross_encoder_failed:
        return None
    try:
        from fastembed.rerank.cross_encoder import TextCrossEncoder
        _cross_encoder = TextCrossEncoder(model_name="Xenova/ms-marco-MiniLM-L-6-v2")
        logger.info("cross_encoder_loaded", model="Xenova/ms-marco-MiniLM-L-6-v2")
        return _cross_encoder
    except Exception as exc:
        _cross_encoder_failed = True
        logger.warning("cross_encoder_load_failed_using_lexical_fallback", error=str(exc))
        return None


def _lexical_fallback(query: str, texts: list[str]) -> list[float]:
    query_terms = set(tokenize(query))
    if not query_terms:
        return [0.0] * len(texts)
    return [
        len(query_terms & set(tokenize(t))) / len(query_terms)
        for t in texts
    ]


def lexical_rerank(query: str, texts: list[str]) -> list[float]:
    """
    Score query-document pairs using BAAI/bge-reranker-base cross-encoder.
    Falls back to lexical overlap if the model is unavailable.
    """
    if not texts:
        return []

    model = _get_cross_encoder()
    if model is None:
        return _lexical_fallback(query, texts)

    try:
        scores = list(model.rerank(query, texts))
        # fastembed returns floats directly
        return [float(s) for s in scores]
    except Exception as exc:
        logger.warning("cross_encoder_rerank_failed", error=str(exc))
        return _lexical_fallback(query, texts)
