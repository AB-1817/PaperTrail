from __future__ import annotations

from functools import lru_cache

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── Environment ──────────────────────────────────────────────────────────
    environment: str = "development"
    log_level: str = "INFO"

    # ── Supabase ─────────────────────────────────────────────────────────────
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_jwt_issuer: str  # https://<project>.supabase.co/auth/v1
    supabase_jwt_secret: str = ""  # HS256 secret; leave empty if RS256

    # ── Database (direct / session pooler — NOT transaction pooler) ──────────
    database_url: str  # postgresql+asyncpg://...

    # ── Qdrant ───────────────────────────────────────────────────────────────
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""

    # ── Redis ────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379"

    # ── Provider APIs ────────────────────────────────────────────────────────
    semantic_scholar_api_key: str = ""
    openalex_email: str = ""
    crossref_email: str = ""
    unpaywall_email: str = ""

    # ── LLM ──────────────────────────────────────────────────────────────────
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    papertrail_llm_provider: str = "ollama"  # ollama | openai | anthropic

    # ── Embeddings ───────────────────────────────────────────────────────────
    embedding_model: str = "BAAI/bge-base-en-v1.5"
    embedding_model_version: str = "1.5.0"
    embedding_dimensions: int = 768
    # hash keeps local runs and CI off the 500MB weight download.
    # Set to fastembed to encode with BAAI/bge-base-en-v1.5.
    embedding_backend: str = "hash"
    reranker_model: str = "BAAI/bge-reranker-base"
    bm25_model: str = "Qdrant/bm25"
    bm25_k1: float = 1.2
    bm25_b: float = 0.75
    grobid_url: str = "http://localhost:8070"

    # ── Security ─────────────────────────────────────────────────────────────
    allowed_origins: str = "http://localhost:3000"
    pdf_fetch_allowed_domains: str = "arxiv.org,export.arxiv.org,europepmc.org"

    # ── Sentry ───────────────────────────────────────────────────────────────
    sentry_dsn: str = ""

    # ── Derived ──────────────────────────────────────────────────────────────
    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def pdf_allowed_domains_list(self) -> list[str]:
        return [d.strip() for d in self.pdf_fetch_allowed_domains.split(",") if d.strip()]

    @field_validator("database_url")
    @classmethod
    def reject_transaction_pooler(cls, v: str) -> str:
        if ":6543" in v:
            raise ValueError(
                "DATABASE_URL must not use port 6543 (transaction pooler). "
                "Use port 5432 (direct connection or session pooler). "
                "See ADR-007."
            )
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
