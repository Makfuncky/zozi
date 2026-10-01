"""Country-detection adapter for the middleware layer.

The circuit allows middleware to import only ``db``, ``utils``,
``dependencies`` and ``data`` — never ``services``. This adapter owns
the IP -> country lookup (delegated to ``providers.geography.ip``) so
``middleware.country_context`` stays inside the circuit.

Behavior matches the previous in-middleware implementation: the
request IP is extracted from the standard headers, private/reserved
ranges are skipped, and ``None`` is returned when the country cannot
be resolved.
"""
from __future__ import annotations

from typing import Optional


def _extract_ip(headers: dict, fallback_ip: Optional[str]) -> Optional[str]:
    for header in ("x-forwarded-for", "x-real-ip", "cf-connecting-ip"):
        value = headers.get(header) or headers.get(header.title())
        if value:
            return str(value).split(",")[0].strip()
    return fallback_ip


def _is_private_ip(ip: Optional[str]) -> bool:
    if not ip:
        return True
    return ip.startswith(("127.", "10.", "192.168.", "172.16.", "::1"))


def _lookup_country(ip: str) -> Optional[str]:
    try:
        from providers.geography.ip import detect_country_from_ip
        country = detect_country_from_ip(ip)
    except Exception:
        return None
    if not country or country == "XX":
        return None
    return country.upper()


def detect_country_from_ip(
    headers: dict,
    client_ip: Optional[str],
) -> Optional[str]:
    """Return the ISO country code for a request IP, or None when unresolved."""
    if not client_ip:
        return None
    try:
        ip = _extract_ip(headers, client_ip)
        if ip and not _is_private_ip(ip):
            return _lookup_country(ip)
    except Exception:
        return None
    return None
