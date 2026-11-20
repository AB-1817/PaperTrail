from __future__ import annotations

import hashlib

import httpx

from app.core.security import validate_pdf_url


async def download_pdf(url: str, max_size_bytes: int = 52_428_800) -> tuple[bytes, str]:
    """
    Safely download an open access PDF with SSRF protection and size limit.
    Returns (content_bytes, sha256_hex).
    """
    validated_url = validate_pdf_url(url)

    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        response = await client.get(validated_url)
        response.raise_for_status()

        content = response.content
        if len(content) > max_size_bytes:
            raise ValueError(f"PDF exceeds size limit of {max_size_bytes} bytes")

        sha256 = hashlib.sha256(content).hexdigest()
        return content, sha256
