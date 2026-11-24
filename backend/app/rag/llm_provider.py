from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx

from app.core.config import get_settings
from app.core.errors import AppError


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

    def __init__(
        self, base_url: str = "http://localhost:11434", model: str = "llama3.1:8b"
    ) -> None:
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
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            raise AppError(
                status_code=503, code="LLM_NOT_CONFIGURED", message=f"Ollama unreachable: {exc}"
            ) from exc

        return LLMResponse(
            content=data.get("message", {}).get("content", ""),
            model_id=self.model_id,
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            finish_reason="stop",
        )


class OpenAIProvider:
    provider_name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self.api_key = api_key
        self.model_id = model

    async def complete(
        self,
        messages: list[Message],
        max_tokens: int = 2000,
        temperature: float = 0.0,
    ) -> LLMResponse:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model_id,
                        "messages": [{"role": m.role, "content": m.content} for m in messages],
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    },
                )
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            raise AppError(
                status_code=503, code="LLM_NOT_CONFIGURED", message=f"OpenAI error: {exc}"
            ) from exc

        choice = data["choices"][0]
        usage = data.get("usage") or {}
        return LLMResponse(
            content=choice["message"]["content"],
            model_id=self.model_id,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            finish_reason=choice.get("finish_reason", "stop"),
        )


class AnthropicProvider:
    provider_name = "anthropic"

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-latest") -> None:
        self.api_key = api_key
        self.model_id = model

    async def complete(
        self,
        messages: list[Message],
        max_tokens: int = 2000,
        temperature: float = 0.0,
    ) -> LLMResponse:
        system = "\n\n".join(m.content for m in messages if m.role == "system")
        conversation = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role in ("user", "assistant")
        ]
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                    },
                    json={
                        "model": self.model_id,
                        "system": system,
                        "messages": conversation,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    },
                )
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            raise AppError(
                status_code=503, code="LLM_NOT_CONFIGURED", message=f"Anthropic error: {exc}"
            ) from exc

        content = "".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        )
        usage = data.get("usage") or {}
        return LLMResponse(
            content=content,
            model_id=self.model_id,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            finish_reason=data.get("stop_reason", "stop"),
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


class OpenAICompatProvider:
    """Generic OpenAI-compatible provider (Groq, Gemini, OmniRoute, etc.)"""

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model_id = model
        self.provider_name = "openai_compat"

    async def complete(
        self,
        messages: list[Message],
        max_tokens: int = 2000,
        temperature: float = 0.0,
    ) -> LLMResponse:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model_id,
                        "messages": [{"role": m.role, "content": m.content} for m in messages],
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    },
                )
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            raise AppError(
                status_code=503, code="LLM_NOT_CONFIGURED", message=f"{self.provider_name} error: {exc}"
            ) from exc

        choice = data["choices"][0]
        usage = data.get("usage") or {}
        return LLMResponse(
            content=choice["message"]["content"],
            model_id=self.model_id,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            finish_reason=choice.get("finish_reason", "stop"),
        )


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    provider = settings.llm_provider.lower()

    if settings.environment == "test":
        if provider == "mock":
            return MockProvider()

    if provider == "ollama":
        return OllamaProvider(base_url=settings.ollama_base_url)
    if provider == "openai":
        if not settings.openai_api_key:
            raise AppError(status_code=503, code="LLM_NOT_CONFIGURED", message="LLM provider not configured")
        return OpenAIProvider(api_key=settings.openai_api_key)
    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise AppError(status_code=503, code="LLM_NOT_CONFIGURED", message="LLM provider not configured")
        return AnthropicProvider(api_key=settings.anthropic_api_key)
    if provider == "groq":
        if not settings.groq_api_key:
            raise AppError(status_code=503, code="LLM_NOT_CONFIGURED", message="GROQ_API_KEY not set")
        return OpenAICompatProvider(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
            model=settings.groq_model,
        )
    if provider == "gemini":
        if not settings.gemini_api_key:
            raise AppError(status_code=503, code="LLM_NOT_CONFIGURED", message="GEMINI_API_KEY not set")
        return OpenAICompatProvider(
            api_key=settings.gemini_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai",
            model=settings.gemini_model,
        )
    if provider == "openai_compat":
        return OpenAICompatProvider(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.openai_model,
        )

    if settings.environment == "test":
        return MockProvider()

    raise AppError(
        status_code=503, code="LLM_NOT_CONFIGURED", message="LLM provider not configured"
    )
