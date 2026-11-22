from __future__ import annotations

import json

from app.rag.llm_provider import Message, get_llm_provider


async def validate_semantic(claim: str, passage: str) -> dict[str, object]:
    """Layer 2: ask the configured LLM whether the passage entails the claim."""
    if not claim or not passage:
        return {
            "entailment_score": 0.0,
            "supports": False,
            "contradicts": False,
            "semantic_valid": False,
            "validation_method": "token_overlap",
        }

    prompt = (
        "Determine whether the passage entails or supports the claim. "
        "Return only strict JSON with keys entailment_score, supports, contradicts. "
        "entailment_score must be between 0 and 1. "
        f"CLAIM: {claim}\nPASSAGE: {passage}"
    )
    try:
        provider = get_llm_provider()
        response = await provider.complete(
            [
                Message(
                    role="system", content="You are a precise natural-language inference evaluator."
                ),
                Message(role="user", content=prompt),
            ],
            max_tokens=200,
            temperature=0.0,
        )
        parsed = json.loads(response.content.strip().strip("`"))
        score = max(0.0, min(1.0, float(parsed.get("entailment_score", 0.0))))
        supports = bool(parsed.get("supports", False)) and score >= 0.70
        contradicts = bool(parsed.get("contradicts", False))
        return {
            "entailment_score": round(score, 4),
            "supports": supports,
            "contradicts": contradicts,
            "semantic_valid": supports and not contradicts,
            "validation_method": "llm_nli",
        }
    except Exception:
        # Fail closed: no claim is marked supported when semantic verification is unavailable.
        return {
            "entailment_score": 0.0,
            "supports": False,
            "contradicts": False,
            "semantic_valid": False,
            "validation_method": "llm_nli_unavailable",
        }
