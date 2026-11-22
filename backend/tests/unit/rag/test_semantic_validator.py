from __future__ import annotations

import pytest

from app.rag import semantic_validator


@pytest.mark.asyncio
async def test_semantic_validation_fails_closed_when_provider_unavailable(monkeypatch):
    def unavailable():
        raise RuntimeError("LLM provider is not configured")

    monkeypatch.setattr(semantic_validator, "get_llm_provider", unavailable)
    result = await semantic_validator.validate_semantic(
        "The study reports a 10 percent improvement.",
        "The passage discusses the experimental setup.",
    )

    assert result["semantic_valid"] is False
    assert result["supports"] is False
    assert result["entailment_score"] == 0.0
