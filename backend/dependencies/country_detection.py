"""Country-detection adapter for the middleware layer.

The circuit allows middleware to import only ``db``, ``utils``,
``dependencies`` and ``data`` — never ``services``. This adapter owns the
``services.geography.country_detection`` call (the dependencies layer is permitted to
reach services), so ``middleware.country_context`` stays inside the circuit.

Behavior matches the previous in-middleware implementation exactly: the
request IP is extracted from the standard headers, private/reserved ranges are
skipped, and ``None`` is returned when the country cannot be resolved (so the
caller falls back to its other detection strategies).
"""
from __future__ import annotations

from typing import Optional

_service = None


def _get_service():
    global _service
    if _service is None:
        from services.geography.country_detection import CountryDetectionService
        _service = CountryDetectionService()
    return _service


def detect_country_from_ip(
    headers: dict,
    client_ip: Optional[str],
) -> Optional[str]:
    """Return the ISO country code for a request IP, or None when unresolved."""
    if not client_ip:
        return None
    try:
        svc = _get_service()
        ip = svc._extract_ip(headers, client_ip)
        if ip and not svc._is_private_ip(ip):
            country, _ = svc._lookup_country_by_ip(ip)
            return country or None
    except Exception:
        return None
    return None
