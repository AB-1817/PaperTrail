from __future__ import annotations

import re


def validate_semantic(claim: str, passage: str) -> dict[str, object]:
    """
    Layer 2: Semantic Evidence Support Validation.
    Computes entailment / support score between claim and passage.
    """
    if not claim or not passage:
        return {
            "entailment_score": 0.0,
            "supports": False,
            "contradicts": False,
            "semantic_valid": False,
            "validation_method": "token_overlap",
        }

    def tokenize(s: str) -> set[str]:
        return set(re.findall(r"\w+", s.lower()))

    claim_tokens = tokenize(claim)
    passage_tokens = tokenize(passage)

    if not claim_tokens:
        return {
            "entailment_score": 0.0,
            "supports": False,
            "contradicts": False,
            "semantic_valid": False,
            "validation_method": "token_overlap",
        }

    overlap = claim_tokens & passage_tokens
    score = len(overlap) / len(claim_tokens)

    # Threshold for semantic support
    supports = score >= 0.35

    return {
        "entailment_score": round(score, 4),
        "supports": supports,
        "contradicts": False,
        "semantic_valid": supports,
        "validation_method": "token_overlap",
    }
