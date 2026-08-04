"""Background Check Service — watchlist / sanctions / dangerous-goods screening.

Queries an external watchlist API (simulated for development; real endpoint
in production) to determine whether a candidate is cleared for onboarding.
If flagged, the onboarding pipeline transitions to ``blocked`` status.

Usage::

    result = run_background_check(
        employee_code="EMP0001",
        full_name="John Doe",
        country_code="OM",
    )
    # result = {"status": "clear", ...}  or  {"status": "flagged", ...}
"""

__all__ = [
    "run_background_check",
    "BACKGROUND_CHECK_CLEAR",
    "BACKGROUND_CHECK_FLAGGED",
    "BACKGROUND_CHECK_ERROR",
]

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import URLError

from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)

# ── Result constants ─────────────────────────────────────────

BACKGROUND_CHECK_CLEAR = "clear"
BACKGROUND_CHECK_FLAGGED = "flagged"
BACKGROUND_CHECK_ERROR = "error"

# ── Watchlist data (simulated) ────────────────────────────────
# In production this data comes from a third-party API.  Here we
# hard-code a few "known bad" names so the behaviour is testable
# without network calls.

_KNOWN_FLAGGED_NAMES: set[str] = {
    "john doe flagged",
    "jane blacklisted",
    "sanctions target",
    "dangerous goods operative",
    "restricted party",
    "terrorist financing suspect",
    "money laundering associate",
}

_KNOWN_FLAGGED_CODES: set[str] = {
    "BANNED-001",
    "BLACKLIST-002",
    "SANCTION-003",
}


# ── Public API ────────────────────────────────────────────────


@dataclass
class BackgroundCheckResult:
    """Result of a background / watchlist screening."""

    status: str                       # clear | flagged | error
    employee_code: str
    full_name: str
    country_code: str
    score: float                      # 0.0 = clean, 1.0 = certain match
    details: str                      # human-readable summary
    flagged_categories: list[str] = field(default_factory=list)
    checked_at: str = field(default_factory=lambda: _utcnow().isoformat())
    check_id: Optional[str] = None    # external API reference

    def to_dict(self) -> dict:
        return asdict(self)


# ── Main entry point ──────────────────────────────────────────


def run_background_check(
    employee_code: str,
    full_name: str,
    country_code: str = "OM",
) -> BackgroundCheckResult:
    """Screen *employee* against the configured watchlist API.

    In development mode (``APP_ENV=test`` or ``WATCHLIST_API_URL`` unset) a
    built-in simulated check is used so tests and local dev work without
    network calls.

    In production set ``WATCHLIST_API_URL`` in the environment to point at
    your preferred screening provider (e.g. LexisNexis, Onfido, World-Check).
    """
    if _use_simulated():
        return _simulated_check(employee_code, full_name, country_code)

    return _api_check(employee_code, full_name, country_code)


# ── Internal helpers ──────────────────────────────────────────


def _use_simulated() -> bool:
    """Return True when no real watchlist endpoint is configured."""
    api_url = os.environ.get("WATCHLIST_API_URL", "").strip()
    env = os.environ.get("APP_ENV", "development")
    return not api_url or env in ("test", "development")


def _simulated_check(
    employee_code: str,
    full_name: str,
    country_code: str,
) -> BackgroundCheckResult:
    """Built-in simulated check — no network call.

    Flagged if the name appears in the hard-coded watchlist.  Otherwise clear.
    Sanctions countries and high-risk jurisdictions also add advisory notes.
    """
    name_lower = full_name.strip().lower()
    code_upper = employee_code.strip().upper()

    matches: list[str] = []

    # Name-based watchlist
    if name_lower in _KNOWN_FLAGGED_NAMES:
        matches.append(f"Name matches watchlist entry: {full_name!r}")

    # Code-based watchlist
    if code_upper in _KNOWN_FLAGGED_CODES:
        matches.append(f"Employee code matches sanctions list: {employee_code!r}")

    # Country risk advisory (not a block, just a note)
    high_risk_countries = {"IR", "KP", "SY", "CU", "SD"}
    country_flagged = country_code.strip().upper() in high_risk_countries
    if country_flagged:
        matches.append(f"Country {country_code} is on the high-risk advisory list")

    if matches:
        return BackgroundCheckResult(
            status=BACKGROUND_CHECK_FLAGGED,
            employee_code=employee_code,
            full_name=full_name,
            country_code=country_code,
            score=0.92,
            details="; ".join(matches),
            flagged_categories=["watchlist"] + (["sanctions_country"] if country_flagged else []),
        )

    return BackgroundCheckResult(
        status=BACKGROUND_CHECK_CLEAR,
        employee_code=employee_code,
        full_name=full_name,
        country_code=country_code,
        score=0.0,
        details="No watchlist match found",
        flagged_categories=[],
    )


def _api_check(
    employee_code: str,
    full_name: str,
    country_code: str,
) -> BackgroundCheckResult:
    """Query the real external watchlist API."""
    api_url = os.environ["WATCHLIST_API_URL"].rstrip("/")
    payload = json.dumps({
        "employee_code": employee_code,
        "full_name": full_name,
        "country_code": country_code,
        "timestamp": _utcnow().isoformat(),
    }).encode()

    try:
        req = Request(
            f"{api_url}/v1/screen",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode())

        return BackgroundCheckResult(
            status=body.get("status", BACKGROUND_CHECK_ERROR),
            employee_code=employee_code,
            full_name=full_name,
            country_code=country_code,
            score=float(body.get("score", 0.0)),
            details=body.get("details", "External check completed"),
            flagged_categories=body.get("flagged_categories", []),
            check_id=body.get("check_id"),
        )
    except (URLError, json.JSONDecodeError, KeyError) as exc:
        logger.warning("Watchlist API call failed for %s: %s", employee_code, exc)
        return BackgroundCheckResult(
            status=BACKGROUND_CHECK_ERROR,
            employee_code=employee_code,
            full_name=full_name,
            country_code=country_code,
            score=0.0,
            details=f"API error: {exc}",
            flagged_categories=[],
        )
