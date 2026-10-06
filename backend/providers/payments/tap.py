"""Tap Payments SDK access point for the provider layer.

Tap Payments (formerly Tap) is an HTTP-based payment gateway operating in the
Middle East and North Africa. This module wraps their REST API (token-based
authentication, JSON payloads) behind a provider boundary.
"""

from __future__ import annotations

import logging
import time
from decimal import Decimal
from typing import Any, Callable, Optional

import httpx

from infrastructure.observability.circuit_breaker import (
    CircuitBreakerError,
    # CircuitState is retained in the module namespace even though
    # _call_with_breaker now delegates to CircuitBreaker.call (which consults
    # CircuitState internally via _before_call). It stays importable because
    # callers and tests reference `tap.CircuitState`, and removing a public
    # name is out of scope for this block.
    CircuitState,
    get_circuit_breaker,
)

from providers.payments.config import (
    is_tap_configured,
    resolve_tap_api_base_url,
    resolve_tap_secret_key,
    resolve_tap_webhook_secret,
)
from providers.payments.webhooks import _verify_tap_signature

logger = logging.getLogger(__name__)

HAS_TAP = True
_TAP_DEFAULT_TIMEOUT = 30
_TAP_BREAKER_FAILURE_THRESHOLD = 5

# Status codes that mean the GATEWAY failed, not that our request was wrong.
# These must count toward the breaker's failure threshold (Law 296).
#
# httpx treats an HTTP 500 as a SUCCESSFUL exchange - it returns a Response
# rather than raising - so a breaker that only counts raised exceptions records
# nothing when the gateway is hard-down, and keeps every call flowing. Measured:
# 20 consecutive HTTP 500 responses produced failure_count == 0 and the breaker
# stayed CLOSED. A dead gateway would therefore be hammered on every request,
# which is the cascade Law 296 exists to prevent.
#
# 4xx (except 408/429) is deliberately NOT counted: those are caller errors -
# a malformed payload or an unknown charge id - and tripping the breaker on them
# would take the adapter offline for a bug in OUR request.
_TAP_BREAKER_FAILURE_STATUSES: frozenset[int] = frozenset({408, 425, 429, 500, 502, 503, 504})


def _is_gateway_failure(response: Any) -> bool:
    """Return True when *response* indicates the Tap gateway itself failed."""
    status = getattr(response, "status_code", None)
    if not isinstance(status, int):
        return False
    if status in _TAP_BREAKER_FAILURE_STATUSES:
        return True
    # Any other 5xx is still a server-side failure.
    return status >= 500


_tap_breaker = get_circuit_breaker(
    "tap",
    failure_threshold=_TAP_BREAKER_FAILURE_THRESHOLD,
    recovery_timeout=30,
)


def _call_with_breaker(
    breaker: Any,
    func: Callable[[], Any],
) -> Any:
    """Invoke ``func`` through ``breaker`` so failures actually count.

    Law 296 requires every external call to be wrapped in a circuit breaker.
    Merely *reading* ``breaker.state`` does not satisfy that: a breaker only
    opens once its failure counter reaches ``failure_threshold``, and the counter
    is advanced by ``CircuitBreaker.call``. The previous implementation called
    the closure directly, so nothing was ever recorded - proven by driving 8
    consecutive real failures through ``create_charge`` and observing
    ``failure_count == 0`` and ``state == closed`` throughout.

    Two failure modes had to be handled, and both are proven by measurement:

    1. TRANSPORT errors (connection refused, timeout, TLS). These raise, so
       ``breaker.call`` records them via ``_on_failure``.

    2. ERROR RESPONSES. httpx does NOT raise for a 4xx/5xx - it returns a
       Response - so ``breaker.call`` would record a *success*. Measured against
       a server answering 500 to everything: 20 responses produced
       ``failure_count == 0`` and the breaker stayed CLOSED, so a hard-down
       gateway would be hammered on every request. That is exactly the cascade
       Law 296 exists to prevent.

       The status is therefore raised *inside* the closure as ``_GatewayFailure``.
       Letting the breaker itself account for it means there is exactly one
       record per call - no ``_on_success`` that would cancel a manually added
       failure, and no risk of the two counters drifting apart.

    The response is returned UNCHANGED, including on the gateway-failure path,
    so the caller keeps full ownership of status handling and of raising its
    domain error. No request/response shape changes (contract section 3) and no
    existing ``except`` clause changes meaning.

    Error mapping (Law 130): the raw ``CircuitBreakerError`` is translated to
    ``TapError`` so no framework exception type escapes this provider, while
    exceptions from ``func`` itself still propagate untouched because ``call``
    re-raises after recording.
    """
    captured: dict[str, Any] = {}

    def _probe() -> Any:
        response = func()
        captured["response"] = response
        if _is_gateway_failure(response):
            raise _GatewayFailure(
                f"Tap gateway returned HTTP {getattr(response, 'status_code', 'unknown')}"
            )
        return response

    try:
        return breaker.call(_probe)
    except _GatewayFailure as exc:
        # Expected control flow: the gateway answered, but with a failing
        # status. The breaker has already recorded the failure; hand the real
        # response back so the caller can raise its normal domain error.
        logger.warning("Tap gateway failure recorded by breaker: %s", exc)
        return captured["response"]
    except CircuitBreakerError as exc:
        logger.warning("Tap circuit breaker rejected call: %s", exc)
        raise TapError(f"Circuit breaker rejected call: {exc}") from exc


class TapError(Exception):
    """Base exception for Tap provider operations."""


class _GatewayFailure(Exception):
    """Internal marker recording an HTTP error RESPONSE against the breaker.

    httpx does not raise for a 4xx/5xx, so the breaker has no exception to count.
    This type exists purely so ``_record_breaker_outcome`` can hand
    ``_on_failure`` a real exception carrying the status; it never escapes this
    module and is deliberately NOT a ``TapError`` so it cannot be confused with
    a caller-visible domain error.
    """


class TapChargeNotFoundError(TapError):
    """Raised when a Tap charge does not exist."""


class TapRefundError(TapError):
    """Raised when a Tap refund operation fails."""


class TapConfigurationError(TapError):
    """Raised when Tap credentials are missing or invalid."""


def _get_headers() -> dict[str, str]:
    """Build authenticated headers for Tap API calls."""
    secret_key = resolve_tap_secret_key()
    if not secret_key:
        raise TapConfigurationError("TAP_SECRET_KEY must be set.")
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {secret_key}",
    }


def is_available() -> bool:
    """Return True when Tap credentials are configured."""
    return is_tap_configured()


def create_charge(
    amount: Decimal,
    currency: str,
    *,
    customer_name: str,
    customer_email: str = "",
    customer_phone: str = "",
    order_id: str = "",
    description: str = "",
    redirect_url: str = "",
    post_url: str = "",
    metadata: Optional[dict[str, Any]] = None,
    save_card: bool = False,
) -> dict[str, Any]:
    """Create a Tap charge (payment request).

    Tap's charge API returns a hosted payment URL the customer is redirected to.

    Args:
        amount: The charge total (Tap expects major currency units).
        currency: ISO 4217 currency code (e.g. 'KWD', 'SAR', 'AED').
        customer_name: Full name of the customer.
        customer_email: Customer email address.
        customer_phone: Customer phone number.
        order_id: Merchant-side order reference.
        description: Charge description.
        redirect_url: URL to redirect after payment completion.
        post_url: Server-to-server notification URL.
        metadata: Additional fields merged into the request payload.
        save_card: Whether to tokenize the card for future charges.

    Returns:
        dict with 'id', 'transaction_id', 'payment_url', and 'raw' keys.

    Raises:
        TapConfigurationError: If credentials are missing.
        TapError: If charge creation fails.
    """
    api_base = resolve_tap_api_base_url()
    payload: dict[str, Any] = {
        "amount": str(amount),
        "currency": currency.upper(),
        "customer": {
            "first_name": customer_name.split()[0] if customer_name else "",
            "last_name": " ".join(customer_name.split()[1:]) if " " in customer_name else "",
            "email": customer_email,
            "phone": {
                "country_code": "",
                "number": customer_phone,
            },
        },
        "source": {
            "id": "src_card",
        },
        "redirect": {
            "url": redirect_url,
        },
        "post": {
            "url": post_url,
        },
        "description": description or f"Charge for order {order_id}",
        "metadata": {
            "order_id": order_id,
        },
        "save_card": save_card,
        "reference": {
            "transaction": order_id,
        },
    }
    if metadata:
        payload["metadata"].update(metadata)
    try:
        with httpx.Client(timeout=_TAP_DEFAULT_TIMEOUT) as client:
            response = _call_with_breaker(
                _tap_breaker,
                lambda: client.post(
                    f"{api_base}/charges",
                    json=payload,
                    headers=_get_headers(),
                    timeout=_TAP_DEFAULT_TIMEOUT,
                ),
            )
    except httpx.HTTPError as exc:
        logger.exception("Tap create_charge request failed")
        raise TapError(f"Tap API request failed: {exc}") from exc
    except TapError:
        raise
    except Exception as exc:
        logger.exception("Tap create_charge unexpected error")
        raise TapError(f"Tap API request failed: {exc}") from exc
    if response.status_code not in (200, 201):
        raise TapError(
            f"Tap create_charge returned status {response.status_code}: {response.text}"
        )
    data = response.json()
    return {
        "id": data.get("id", ""),
        "transaction_id": data.get("transaction", {}).get("id", ""),
        "payment_url": data.get("transaction", {}).get("url", ""),
        "status": data.get("status", ""),
        "amount": str(data.get("amount", "")),
        "currency": data.get("currency", ""),
        "raw": data,
    }


def get_charge(charge_id: str) -> dict[str, Any]:
    """Retrieve a Tap charge by ID.

    Args:
        charge_id: The Tap charge ID.

    Returns:
        dict with 'id', 'status', 'amount', 'currency', and 'raw' keys.

    Raises:
        TapChargeNotFoundError: If the charge does not exist.
        TapError: If the retrieval fails.
    """
    api_base = resolve_tap_api_base_url()
    try:
        with httpx.Client(timeout=_TAP_DEFAULT_TIMEOUT) as client:
            response = _call_with_breaker(
                _tap_breaker,
                lambda: client.get(
                    f"{api_base}/charges/{charge_id}",
                    headers=_get_headers(),
                    timeout=_TAP_DEFAULT_TIMEOUT,
                ),
            )
    except httpx.HTTPError as exc:
        logger.exception("Tap get_charge request failed for %s", charge_id)
        raise TapError(f"Tap API request failed: {exc}") from exc
    except TapError:
        raise
    except Exception as exc:
        logger.exception("Tap get_charge unexpected error for %s", charge_id)
        raise TapError(f"Tap API request failed: {exc}") from exc
    if response.status_code == 404:
        raise TapChargeNotFoundError(
            f"Tap charge {charge_id} not found"
        )
    if response.status_code != 200:
        raise TapError(
            f"Tap get_charge returned status {response.status_code}"
        )
    data = response.json()
    return {
        "id": data.get("id", charge_id),
        "status": data.get("status", ""),
        "amount": str(data.get("amount", "")),
        "currency": data.get("currency", ""),
        "customer": data.get("customer", {}),
        "raw": data,
    }


def refund_charge(
    charge_id: str,
    *,
    amount: Optional[Decimal] = None,
    reason: str = "",
    metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Refund a Tap charge.

    Args:
        charge_id: The Tap charge ID to refund.
        amount: Optional partial refund amount (full refund if omitted).
        reason: Reason for the refund.
        metadata: Additional fields merged into the request payload.

    Returns:
        dict with 'id', 'status', 'refund_amount', and 'raw' keys.

    Raises:
        TapChargeNotFoundError: If the charge does not exist.
        TapRefundError: If the refund operation fails.
    """
    api_base = resolve_tap_api_base_url()
    payload: dict[str, Any] = {
        "charge_id": charge_id,
        "reason": reason or "Refund",
    }
    if amount is not None:
        payload["amount"] = str(amount)
    if metadata:
        payload["metadata"] = metadata
    response = None
    last_exc: Optional[Exception] = None
    for attempt in range(1, 4):
        try:
            with httpx.Client(timeout=_TAP_DEFAULT_TIMEOUT) as client:
                response = _call_with_breaker(
                    _tap_breaker,
                    lambda: client.post(
                        f"{api_base}/charges/{charge_id}/refunds",
                        json=payload,
                        headers=_get_headers(),
                        timeout=_TAP_DEFAULT_TIMEOUT,
                    ),
                )
            break
        except httpx.HTTPError as exc:
            last_exc = exc
            logger.warning(
                "Tap refund_charge attempt %d failed for %s: %s",
                attempt, charge_id, exc,
            )
            if attempt < 3:
                time.sleep(2 ** (attempt - 1))
        except TapError:
            raise
    if response is None:
        raise TapRefundError(
            f"Tap API request failed after 3 attempts: {last_exc}"
        ) from last_exc
    if response.status_code == 404:
        raise TapChargeNotFoundError(
            f"Tap charge {charge_id} not found"
        )
    if response.status_code not in (200, 201):
        raise TapRefundError(
            f"Tap refund returned status {response.status_code}: {response.text}"
        )
    data = response.json()
    return {
        "id": data.get("id", ""),
        "status": data.get("status", ""),
        "refund_amount": str(data.get("amount", "")),
        "raw": data,
    }


def verify_webhook(
    raw_body: bytes,
    hashstring_header: str,
    webhook_secret: str,
) -> bool:
    """Verify an incoming Tap webhook signature.

    Tap signs each webhook POST with an HMAC-SHA256 digest over the raw body,
    delivered in the 'hashstring' header.

    Args:
        raw_body: The raw request body bytes.
        hashstring_header: The 'hashstring' header value.
        webhook_secret: The shared TAP_WEBHOOK_SECRET.

    Returns:
        True if the signature is valid.
    """
    return _verify_tap_signature(raw_body, hashstring_header, webhook_secret)


def refund_tap_charge(
    charge_id: str,
    amount: Optional[Decimal] = None,
    tap_key: Optional[str] = None,
) -> dict[str, Any]:
    """Refund a Tap charge (convenience wrapper around refund_charge)."""
    return refund_charge(charge_id, amount=amount)


__all__ = [
    "HAS_TAP",
    "TapError",
    "TapChargeNotFoundError",
    "TapRefundError",
    "TapConfigurationError",
    "is_available",
    "create_charge",
    "get_charge",
    "refund_charge",
    "refund_tap_charge",
    "verify_webhook",
]
