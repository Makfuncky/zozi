"""URL safety helpers used to mitigate SSRF when making outbound HTTP requests.

These helpers centralise the validation that should happen before any code
passes a (possibly caller-influenced) URL to ``requests``, ``httpx``, or
``urllib``. The validation:

* requires an explicit allow-list of URL schemes (default ``https``/``http``),
* optionally restricts the host to a known allow-list, and
* rejects private / loopback / link-local / metadata addresses and obvious
  internal host suffixes so a configured or injected URL cannot be used to hit
  internal infrastructure.
"""
from __future__ import annotations

import ipaddress
import logging
from urllib.parse import urlparse
from typing import Iterable, Optional

logger = logging.getLogger(__name__)

DEFAULT_ALLOWED_SCHEMES: tuple[str, ...] = ("https", "http")

# Hosts that are never reachable over the public internet and must be blocked to
# prevent server-side request forgery to internal infrastructure.
_BLOCKED_HOST_SUFFIXES = (
    ".internal",
    ".local",
    ".localhost",
    ".svc",
    ".cluster.local",
    ".consul",
    ".home.arpa",
)

_BLOCKED_EXACT_HOSTS = {
    "localhost",
    "0.0.0.0",
    "0",
    "::1",
    "::",
    "metadata.google.internal",
    "169.254.169.254",
}


def _is_private_host(hostname: str) -> bool:
    host = hostname.strip().lower()
    if not host:
        return True
    if host in _BLOCKED_EXACT_HOSTS:
        return True
    if any(host.endswith(suffix) for suffix in _BLOCKED_HOST_SUFFIXES):
        return True
    try:
        addr = ipaddress.ip_address(host)
        return (
            addr.is_private
            or addr.is_loopback
            or addr.is_link_local
            or addr.is_reserved
            or addr.is_multicast
            or addr.is_unspecified
        )
    except ValueError:
        logger.exception('_is_private_host: handled ValueError')
        return False


def is_safe_url(
    url: str,
    allowed_schemes: Iterable[str] = DEFAULT_ALLOWED_SCHEMES,
    allowed_hosts: Optional[Iterable[str]] = None,
    block_private: bool = True,
) -> bool:
    """Return ``True`` when *url* is safe to fetch.

    A URL is considered safe when it has an allowed scheme, a resolvable host
    that is not a blocked internal address, and (optionally) a host that is
    present in *allowed_hosts*.
    """
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url)
    except (ValueError, TypeError):
        logger.exception('is_safe_url: handled (ValueError, TypeError)')
        return False

    if parsed.scheme.lower() not in {s.lower() for s in allowed_schemes}:
        return False
    if not parsed.hostname:
        return False
    if block_private and _is_private_host(parsed.hostname):
        return False
    if allowed_hosts is not None:
        lowered = {h.lower() for h in allowed_hosts}
        if parsed.hostname.lower() not in lowered:
            return False
    return True


def require_safe_url(
    url: str,
    allowed_schemes: Iterable[str] = DEFAULT_ALLOWED_SCHEMES,
    allowed_hosts: Optional[Iterable[str]] = None,
    block_private: bool = True,
) -> str:
    """Validate *url* and return it unchanged, raising ``ValueError`` if unsafe.

    Raises:
        ValueError: if the URL fails :func:`is_safe_url`.
    """
    if not is_safe_url(
        url,
        allowed_schemes=allowed_schemes,
        allowed_hosts=allowed_hosts,
        block_private=block_private,
    ):
        logger.warning("Blocked SSRF-unsafe URL: %s", url)
        raise ValueError(f"Refusing to fetch SSRF-unsafe URL: {url!r}")
    return url
