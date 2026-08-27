from __future__ import annotations

"""Finance bank/treasury API provider.

External treasury / bank dispatch HTTP calls (connectivity probe + batch
dispatch) are encapsulated here so the finance transfer service orchestrates
through these helpers instead of performing third-party HTTP requests directly.
"""

import logging
from typing import Any, Dict, Optional

try:
    import requests
    HAS_BANK_API = True
except ImportError:
    HAS_BANK_API = False
    requests = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

_REACHABLE_STATUS_CODES = {200, 201, 202, 204, 401, 403, 404, 405}


class BankApiError(Exception):
    """Raised when a bank API call fails (network or non-2xx response)."""

    def __init__(self, message: str, *, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _endpoint(base_url: str, batch_path: str) -> Optional[str]:
    if base_url.strip() and batch_path.strip():
        return f"{base_url.rstrip('/')}/{batch_path.lstrip('/')}"
    return None


def test_connection(
    base_url: str,
    batch_path: str,
    auth_token: str,
    timeout: float,
) -> Dict[str, Any]:
    """Probe the bank API with an OPTIONS request. Never raises.

    Returns a dict with ``reachable``, ``ok``, ``status_code`` and ``detail``.
    """
    endpoint = _endpoint(base_url, batch_path)
    if not endpoint:
        return {
            "reachable": False,
            "ok": False,
            "status_code": None,
            "detail": "Bank API base URL and batch path must be configured before testing the connection.",
        }

    headers = {"Authorization": f"Bearer {auth_token}"}
    try:
        response = requests.request("OPTIONS", endpoint, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        return {
            "reachable": False,
            "ok": False,
            "status_code": None,
            "detail": f"Bank API endpoint could not be reached: {exc}",
        }

    reachable = True
    ok = response.status_code in _REACHABLE_STATUS_CODES
    detail = (
        f"Bank API endpoint responded with HTTP {response.status_code}."
        if ok
        else f"Bank API endpoint responded with HTTP {response.status_code}; investigate before live dispatch."
    )
    return {
        "reachable": reachable,
        "ok": ok,
        "status_code": response.status_code,
        "detail": detail,
    }


def dispatch_batch(
    base_url: str,
    batch_path: str,
    auth_token: str,
    idempotency_key: str,
    payload: Dict[str, Any],
    timeout: float,
) -> Dict[str, Any]:
    """Dispatch a transfer batch to the configured bank API.

    Returns ``{"status_code": int, "body": dict}``. Raises ``BankApiError`` on
    network failure or a non-2xx response so the caller can surface it as an
    HTTP error.
    """
    endpoint = _endpoint(base_url, batch_path)
    if not endpoint:
        raise BankApiError("Bank API base URL and batch path must be configured.")

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
        "Idempotency-Key": idempotency_key,
    }
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise BankApiError(f"Bank API dispatch failed: {exc}") from exc

    body: Dict[str, Any] = {}
    try:
        body = response.json() if response.content else {}
    except ValueError:
        body = {}
    return {"status_code": response.status_code, "body": body}


__all__ = ["BankApiError", "test_connection", "dispatch_batch", "HAS_BANK_API"]
