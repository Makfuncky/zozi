"""Watchlist / sanctions screening provider.

Owns the *raw* external HTTP call to the configured screening vendor
(e.g. LexisNexis, Onfido, World-Check). Domain logic such as the
simulated check, scoring thresholds and result shaping stays in
``services.**``; this module only knows how to talk to the vendor.
"""
from __future__ import annotations

import json
import logging
import os
import time

from datetime import datetime, timezone

import httpx

from infrastructure.security.url_security import require_safe_url

logger = logging.getLogger(__name__)

HAS_WATCHLIST = True

_CIRCUIT = {"failures": 0, "last_failure_ts": 0.0, "open": False}
_CIRCUIT_FAILURE_THRESHOLD = 3
_CIRCUIT_COOLDOWN_SECONDS = 30

_REQUEST_TIMEOUT_SECONDS = 15.0


class WatchlistProviderError(Exception):
    """Raised when the external screening API cannot be reached or returns garbage."""


def _allowed_hosts() -> tuple[str, ...] | None:
    raw = os.environ.get("WATCHLIST_API_ALLOWED_HOSTS", "").strip()
    if not raw:
        return None
    return tuple(h.strip().lower() for h in raw.split(",") if h.strip())


def screen_watchlist(
    employee_code: str,
    full_name: str,
    country_code: str,
    *,
    api_url: str | None = None,
) -> dict:
    """Query the external watchlist/sanctions screening API.

    Returns a dict with keys ``status``, ``score``, ``details``,
    ``flagged_categories`` and ``check_id``. Raises
    :class:`WatchlistProviderError` on transport or parse failure.
    """
    base = (api_url or os.environ.get("WATCHLIST_API_URL", "")).strip().rstrip("/")
    if not base:
        raise WatchlistProviderError("WATCHLIST_API_URL is not configured")

    if not HAS_WATCHLIST:
        return {
            "status": "skipped",
            "score": 0.0,
            "details": "Watchlist provider is disabled",
            "flagged_categories": [],
            "check_id": None,
        }

    try:
        url = require_safe_url(
            f"{base}/v1/screen",
            allowed_schemes=("https",),
            allowed_hosts=_allowed_hosts(),
        )
    except ValueError as exc:
        raise WatchlistProviderError(str(exc)) from exc

    if _CIRCUIT["open"]:
        if time.time() - _CIRCUIT["last_failure_ts"] < _CIRCUIT_COOLDOWN_SECONDS:
            raise WatchlistProviderError("Circuit breaker open: watchlist API unavailable")
        _CIRCUIT["open"] = False
        _CIRCUIT["failures"] = 0

    payload = json.dumps({
        "employee_code": employee_code,
        "full_name": full_name,
        "country_code": country_code,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }).encode()

    last_exc = None
    for attempt in range(3):
        try:
            with httpx.Client(timeout=_REQUEST_TIMEOUT_SECONDS) as client:
                response = client.post(
                    url,
                    content=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                body = response.json()
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            last_exc = exc
            _CIRCUIT["failures"] += 1
            _CIRCUIT["last_failure_ts"] = time.time()
            if _CIRCUIT["failures"] >= _CIRCUIT_FAILURE_THRESHOLD:
                _CIRCUIT["open"] = True
            if attempt < 2:
                time.sleep(2 ** attempt)
            continue
        _CIRCUIT["failures"] = 0
        return {
            "status": body.get("status", "error"),
            "score": float(body.get("score", 0.0)),
            "details": body.get("details", "External check completed"),
            "flagged_categories": body.get("flagged_categories", []),
            "check_id": body.get("check_id"),
        }

    raise WatchlistProviderError(str(last_exc)) from last_exc
