from __future__ import annotations

import pytest

from app.core.security import SSRFError, validate_pdf_url


def _patch_domains(monkeypatch, domains: str = "arxiv.org,export.arxiv.org") -> None:
    monkeypatch.setenv("PDF_FETCH_ALLOWED_DOMAINS", domains)
    monkeypatch.setenv("SUPABASE_URL", "http://localhost:54321")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "x")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "x")
    monkeypatch.setenv("SUPABASE_JWT_ISSUER", "http://localhost:54321/auth/v1")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:54322/postgres")
    from app.core.config import get_settings
    get_settings.cache_clear()


def test_valid_arxiv_url(monkeypatch):
    _patch_domains(monkeypatch)
    url = "https://arxiv.org/pdf/1706.03762"
    assert validate_pdf_url(url) == url


def test_valid_export_arxiv_url(monkeypatch):
    _patch_domains(monkeypatch)
    url = "https://export.arxiv.org/pdf/1706.03762"
    assert validate_pdf_url(url) == url


def test_rejects_http(monkeypatch):
    _patch_domains(monkeypatch)
    with pytest.raises(SSRFError, match="HTTPS"):
        validate_pdf_url("http://arxiv.org/pdf/1706.03762")


def test_rejects_credentials_in_url(monkeypatch):
    _patch_domains(monkeypatch)
    with pytest.raises(SSRFError, match="credentials"):
        validate_pdf_url("https://user:pass@arxiv.org/pdf/1706.03762")


def test_rejects_domain_not_in_allowlist(monkeypatch):
    _patch_domains(monkeypatch)
    with pytest.raises(SSRFError, match="allowlist"):
        validate_pdf_url("https://evil.example.com/paper.pdf")


def test_rejects_private_ip_loopback(monkeypatch):
    _patch_domains(monkeypatch, domains="127.0.0.1")
    with pytest.raises(SSRFError, match="private|not permitted"):
        validate_pdf_url("https://127.0.0.1/paper.pdf")


def test_rejects_private_ip_rfc1918(monkeypatch):
    _patch_domains(monkeypatch, domains="192.168.1.1")
    with pytest.raises(SSRFError, match="private|not permitted"):
        validate_pdf_url("https://192.168.1.1/paper.pdf")


def test_rejects_subdomain_not_in_allowlist(monkeypatch):
    _patch_domains(monkeypatch, domains="arxiv.org")
    with pytest.raises(SSRFError, match="allowlist"):
        validate_pdf_url("https://notarxiv.org/paper.pdf")


def test_accepts_subdomain_of_allowed(monkeypatch):
    _patch_domains(monkeypatch, domains="arxiv.org")
    url = "https://export.arxiv.org/pdf/1706.03762"
    assert validate_pdf_url(url) == url
