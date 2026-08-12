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
import urllib.error
import urllib.request

from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)


class WatchlistProviderError(Exception):
    """Raised when the external screening API cannot be reached or returns garbage."""


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

    payload = json.dumps({
        "employee_code": employee_code,
        "full_name": full_name,
        "country_code": country_code,
        "timestamp": _utcnow().isoformat(),
    }).encode()

    try:
        req = urllib.request.Request(
            f"{base}/v1/screen",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError, KeyError) as exc:
        raise WatchlistProviderError(str(exc)) from exc

    return {
        "status": body.get("status", "error"),
        "score": float(body.get("score", 0.0)),
        "details": body.get("details", "External check completed"),
        "flagged_categories": body.get("flagged_categories", []),
        "check_id": body.get("check_id"),
    }
