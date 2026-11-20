from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx

from app.core.config import get_settings


@dataclass
class Message:
    role: str
    content: str


@dataclass
class LLMResponse:
    content: str
    model_id: str
    input_tokens: int
    output_tokens: int
    finish_reason: str


class LLMProvider(Protocol):
    provider_name: str
    model_id: str

    async def complete(
        self,
        messages: list[Message],
        max_tokens: int = 2000,
        temperature: float = 0.0,
    ) -> LLMResponse: ...


class OllamaProvider:
    provider_name = "ollama"

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1:8b") -> None:
        self.base_url = base_url
        self.model_id = model

    async def complete(
        self,
        messages: list[Message],
        max_tokens: int = 2000,
        temperature: float = 0.0,
    ) -> LLMResponse:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model_id,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "options": {"temperature": temperature, "num_predict": max_tokens},
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        return LLMResponse(
            content=data.get("message", {}).get("content", ""),
            model_id=self.model_id,
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            finish_reason="stop",
        )


class MockProvider:
    provider_name = "mock"
    model_id = "mock-grounded-v1"

    async def complete(
        self,
        messages: list[Message],
        max_tokens: int = 2000,
        temperature: float = 0.0,
    ) -> LLMResponse:
        # Extracts chunk_id from messages context if present
        import re

        context = ""
        for m in messages:
            if "[CITATION:" in m.content:
                context = m.content
                break

        matches = re.findall(r"\[CITATION:([^\]]+)\]", context)
        first_cid = matches[0] if matches else "mock-chunk-id"

        reply = (
            f"Based on the empirical findings and experimental setup provided in the evidence, "
            f"the research addresses these limitations effectively [CITATION:{first_cid}]. "
            f"Furthermore, cross-validation results show measurable performance improvements across evaluated domains [CITATION:{first_cid}]."
        )
        return LLMResponse(
            content=reply,
            model_id=self.model_id,
            input_tokens=250,
            output_tokens=50,
            finish_reason="stop",
        )


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.llm_provider == "ollama":
        return OllamaProvider(base_url=settings.ollama_base_url)
    return MockProvider()
