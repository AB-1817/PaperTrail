from __future__ import annotations

import ipaddress
from urllib.parse import urlparse

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# RFC 1918 + loopback + link-local + CGNAT private ranges
_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


class SSRFError(Exception):
    pass


def validate_pdf_url(url: str) -> str:
    """
    Validate a URL before fetching a PDF.

    Raises SSRFError if the URL fails any check.
    Returns the validated URL unchanged.
    """
    settings = get_settings()

    parsed = urlparse(url)

    # Must be HTTPS
    if parsed.scheme != "https":
        raise SSRFError(f"URL must use HTTPS, got scheme '{parsed.scheme}'")

    # Must not contain credentials in the authority
    if parsed.username or parsed.password:
        raise SSRFError("URL must not contain credentials")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFError("URL has no hostname")

    # If the hostname is a raw IP address, reject it unconditionally.
    # Raw IPs are never permitted regardless of the allowlist.
    try:
        addr = ipaddress.ip_address(hostname)
        for network in _PRIVATE_NETWORKS:
            if addr in network:
                raise SSRFError(f"IP address {addr} is in a private range")
        # Non-private raw IP — still reject; only domain names are allowed
        raise SSRFError(f"Raw IP addresses are not permitted: {hostname}")
    except ValueError:
        pass  # hostname is a domain name — continue to allowlist check

    # Must match an allowed domain suffix
    allowed = settings.pdf_allowed_domains_list
    if not any(hostname == d or hostname.endswith(f".{d}") for d in allowed):
        raise SSRFError(
            f"Hostname '{hostname}' is not in the PDF fetch allowlist. " f"Allowed: {allowed}"
        )

    logger.info("ssrf_guard_passed", url=url, hostname=hostname)
    return url
