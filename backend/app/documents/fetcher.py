from __future__ import annotations

import asyncio
import hashlib
import ipaddress
import socket

import httpx

from app.core.security import validate_pdf_url


async def download_pdf(url: str, max_size_bytes: int = 52_428_800) -> tuple[bytes, str]:
    """
    Safely download an open access PDF with SSRF protection and size limit.
    Returns (content_bytes, sha256_hex).
    """
    validated_url = validate_pdf_url(url)

    # Resolve the allowlisted hostname and reject DNS results in private ranges.
    from urllib.parse import urlparse

    hostname = urlparse(validated_url).hostname
    if hostname:
        loop = asyncio.get_running_loop()
        addresses = await loop.run_in_executor(None, socket.getaddrinfo, hostname, None)
        for address in addresses:
            resolved = ipaddress.ip_address(address[4][0])
            if resolved.is_private or resolved.is_loopback or resolved.is_link_local:
                raise ValueError(f"PDF hostname resolved to blocked address: {resolved}")

    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        response = await client.get(validated_url)
        response.raise_for_status()

        content = response.content
        if len(content) > max_size_bytes:
            raise ValueError(f"PDF exceeds size limit of {max_size_bytes} bytes")

        sha256 = hashlib.sha256(content).hexdigest()
        return content, sha256
