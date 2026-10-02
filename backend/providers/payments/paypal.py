"""PayPal REST access point for the provider layer.

PayPal is reached through direct REST calls over httpx (TECHNOLOGY_STACK.md
section 6: no official maintained Python SDK; REST is stable and auditable).
Service-layer code must not perform PayPal HTTP requests directly; it should
reach them through this provider module so that all third-party payment access
is centralized behind the provider boundary.
"""

from __future__ import annotations

import logging
import time
from decimal import Decimal
from typing import Any, Optional

from infrastructure.observability.circuit_breaker import (
    CircuitBreakerError,
    get_circuit_breaker,
)

from providers.payments.config import (
    is_paypal_configured,
    resolve_paypal_credentials,
)

logger = logging.getLogger(__name__)

try:
    import httpx

    HAS_PAYPAL = True
except ImportError:
    httpx = None  # type: ignore[assignment]
    HAS_PAYPAL = False

# Legacy SDK handle retained for backward-compatible introspection; the
# provider no longer imports any PayPal SDK (direct REST via httpx).
_paypal_sdk = None

_PAYPAL_TIMEOUT = 30.0

_PAYPAL_BREAKER_FAILURE_THRESHOLD = 5

_paypal_breaker = get_circuit_breaker(
    "paypal",
    failure_threshold=_PAYPAL_BREAKER_FAILURE_THRESHOLD,
    recovery_timeout=30,
)

_access_token: str = ""
_access_token_expires_at: float = 0.0


class PayPalError(Exception):
    """Base exception for PayPal provider operations."""


class PayPalOrderNotFoundError(PayPalError):
    """Raised when a PayPal order does not exist."""


class PayPalCaptureError(PayPalError):
    """Raised when a PayPal capture operation fails."""


class PayPalRefundError(PayPalError):
    """Raised when a PayPal refund operation fails."""


class PayPalVoidError(PayPalError):
    """Raised when a PayPal void operation fails."""


class PayPalConfigurationError(PayPalError):
    """Raised when PayPal credentials are missing or invalid."""


def _get_sdk() -> Any:
    """Return the underlying PayPal SDK module, or raise if unavailable."""
    if not HAS_PAYPAL:
        raise PayPalConfigurationError(
            "PayPal SDK is not installed. This provider uses direct REST via httpx."
        )
    if _paypal_sdk is not None:
        return _paypal_sdk
    raise PayPalConfigurationError("PayPal SDK client is not available.")


def _get_client() -> Any:
    """Build and return an httpx client bound to the PayPal REST base URL."""
    if httpx is None or not HAS_PAYPAL:
        raise PayPalConfigurationError(
            "PayPal HTTP client is not available. Install 'httpx'."
        )
    client_id, secret, base_url = resolve_paypal_credentials()
    if not client_id or not secret:
        raise PayPalConfigurationError(
            "PAYPAL_CLIENT_ID and PAYPAL_SECRET must be set."
        )
    return httpx.Client(base_url=base_url, timeout=_PAYPAL_TIMEOUT)


def _get_access_token(client: Any) -> str:
    """Return a cached OAuth bearer token, requesting a new one when needed.

    Uses the client-credentials grant at ``/v1/oauth2/token`` with HTTP Basic
    authentication from the configured credentials.
    """
    global _access_token, _access_token_expires_at
    now = time.monotonic()
    if _access_token and now < _access_token_expires_at:
        return _access_token
    client_id, secret, _ = resolve_paypal_credentials()
    if not client_id or not secret:
        raise PayPalConfigurationError(
            "PAYPAL_CLIENT_ID and PAYPAL_SECRET must be set."
        )
    response = client.post(
        "/v1/oauth2/token",
        content="grant_type=client_credentials",
        headers={"Accept": "application/json"},
        auth=(client_id, secret),
    )
    if response.status_code not in (200, 201):
        raise PayPalError(
            f"PayPal token request returned status {response.status_code}"
        )
    payload = response.json()
    token = str(payload.get("access_token") or "")
    if not token:
        raise PayPalError("PayPal token response is missing access_token")
    try:
        expires_in = float(payload.get("expires_in") or 3600.0)
    except (TypeError, ValueError):
        expires_in = 3600.0
    _access_token = token
    _access_token_expires_at = now + max(expires_in - 60.0, 0.0)
    return token


def _request(
    client: Any,
    method: str,
    path: str,
    *,
    json_body: Optional[dict[str, Any]] = None,
    prefer: bool = False,
) -> tuple[int, dict[str, Any]]:
    """Execute one PayPal REST call and return ``(status_code, body)``."""
    token = _get_access_token(client)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    if prefer:
        headers["Prefer"] = "return=representation"
    if json_body is None:
        response = client.request(method, path, headers=headers)
    else:
        response = client.request(method, path, headers=headers, json=json_body)
    try:
        data = response.json()
    except Exception:
        data = None
    if not isinstance(data, dict):
        data = {}
    return response.status_code, data


def is_available() -> bool:
    """Return True when the PayPal HTTP client is importable and credentials are set."""
    return HAS_PAYPAL and is_paypal_configured()


def create_order(
    amount: Decimal,
    currency: str,
    *,
    return_url: str,
    cancel_url: str,
    description: str = "",
    reference_id: str = "",
    metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Create a PayPal order.

    Args:
        amount: The order total.
        currency: ISO 4217 currency code (e.g. 'USD').
        return_url: URL to redirect after approval.
        cancel_url: URL to redirect on cancellation.
        description: Human-readable order description.
        reference_id: Merchant-side reference identifier.
        metadata: Additional key-value pairs attached to the order.

    Returns:
        dict with 'id', 'status', and 'approval_url' keys.

    Raises:
        PayPalConfigurationError: If PayPal client or credentials are missing.
        PayPalError: If order creation fails.
    """
    client = _get_client()
    payload: dict[str, Any] = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id": reference_id,
                "description": description,
                "amount": {
                    "currency_code": currency.upper(),
                    "value": str(amount),
                },
            }
        ],
        "application_context": {
            "return_url": return_url,
            "cancel_url": cancel_url,
        },
    }
    if metadata:
        payload["purchase_units"][0]["custom_id"] = str(metadata)
    if _paypal_breaker.state.value == "open":
        client.close()
        raise PayPalError("PayPal circuit breaker is open")
    try:
        status_code, data = _request(
            client,
            "POST",
            "/v2/checkout/orders",
            json_body=payload,
            prefer=True,
        )
    except CircuitBreakerError as exc:
        logger.warning("PayPal circuit breaker open for create_order: %s", exc)
        raise PayPalError(f"PayPal circuit breaker open: {exc}") from exc
    except Exception as exc:
        logger.exception("PayPal create_order failed")
        raise PayPalError(f"Failed to create PayPal order: {exc}") from exc
    finally:
        client.close()
    if status_code not in (200, 201):
        raise PayPalError(
            f"PayPal create_order returned status {status_code}"
        )
    approval_url = ""
    for link in data.get("links") or []:
        if isinstance(link, dict) and link.get("rel") == "approve":
            approval_url = str(link.get("href") or "")
            break
    return {
        "id": data.get("id"),
        "status": str(data.get("status")),
        "approval_url": approval_url,
        "raw": data,
    }


def capture_payment(
    order_id: str,
    *,
    amount: Optional[Decimal] = None,
    currency: Optional[str] = None,
) -> dict[str, Any]:
    """Capture a previously approved PayPal order.

    Args:
        order_id: The PayPal order ID.
        amount: Optional partial capture amount.
        currency: Required when amount is provided.

    Returns:
        dict with 'id', 'status', and 'capture_amount' keys.

    Raises:
        PayPalOrderNotFoundError: If the order does not exist.
        PayPalCaptureError: If the capture operation fails.
    """
    client = _get_client()
    if _paypal_breaker.state.value == "open":
        client.close()
        raise PayPalCaptureError("PayPal circuit breaker is open")
    body: Optional[dict[str, Any]] = None
    if amount is not None and currency:
        body = {
            "amount": {
                "currency_code": currency.upper(),
                "value": str(amount),
            }
        }
    try:
        status_code, data = _request(
            client,
            "POST",
            f"/v2/checkout/orders/{order_id}/capture",
            json_body=body,
            prefer=True,
        )
    except CircuitBreakerError as exc:
        logger.warning("PayPal circuit breaker open for capture_payment %s: %s", order_id, exc)
        raise PayPalCaptureError(f"PayPal circuit breaker open: {exc}") from exc
    except Exception as exc:
        if "NOT_FOUND" in str(exc) or "404" in str(exc):
            raise PayPalOrderNotFoundError(
                f"PayPal order {order_id} not found"
            ) from exc
        logger.exception("PayPal capture_payment failed for order %s", order_id)
        raise PayPalCaptureError(
            f"Failed to capture PayPal order {order_id}: {exc}"
        ) from exc
    finally:
        client.close()
    if status_code == 404 or "NOT_FOUND" in str(data):
        raise PayPalOrderNotFoundError(
            f"PayPal order {order_id} not found"
        )
    if status_code not in (200, 201):
        raise PayPalCaptureError(
            f"PayPal capture returned status {status_code}"
        )
    capture_amount = str(amount) if amount else ""
    status = str(data.get("status"))
    for pu in data.get("purchase_units") or []:
        if not isinstance(pu, dict):
            continue
        payments = pu.get("payments")
        if payments:
            for cap in payments.get("captures") or []:
                status = str(cap.get("status"))
                cap_amount = cap.get("amount")
                if cap_amount:
                    capture_amount = str(cap_amount.get("value"))
                break
    return {
        "id": data.get("id"),
        "status": status,
        "capture_amount": capture_amount,
        "raw": data,
    }


def refund_payment(
    capture_id: str,
    *,
    amount: Optional[Decimal] = None,
    currency: Optional[str] = None,
    reason: str = "",
) -> dict[str, Any]:
    """Refund a captured PayPal payment.

    Args:
        capture_id: The PayPal capture ID to refund.
        amount: Optional partial refund amount.
        currency: Required when amount is provided.
        reason: Human-readable refund reason.

    Returns:
        dict with 'id', 'status', and 'refund_amount' keys.

    Raises:
        PayPalRefundError: If the refund operation fails.
    """
    client = _get_client()
    if _paypal_breaker.state.value == "open":
        client.close()
        raise PayPalRefundError("PayPal circuit breaker is open")
    body: dict[str, Any] = {}
    if reason:
        body["note_to_payer"] = reason
    if amount is not None and currency:
        body["amount"] = {
            "currency_code": currency.upper(),
            "value": str(amount),
        }
    try:
        status_code, data = _request(
            client,
            "POST",
            f"/v2/payments/captures/{capture_id}/refund",
            json_body=body or None,
            prefer=True,
        )
    except CircuitBreakerError as exc:
        logger.warning("PayPal circuit breaker open for refund_payment %s: %s", capture_id, exc)
        raise PayPalRefundError(f"PayPal circuit breaker open: {exc}") from exc
    except Exception as exc:
        logger.exception("PayPal refund_payment failed for capture %s", capture_id)
        raise PayPalRefundError(
            f"Failed to refund PayPal capture {capture_id}: {exc}"
        ) from exc
    finally:
        client.close()
    if status_code not in (200, 201):
        raise PayPalRefundError(
            f"PayPal refund returned status {status_code}"
        )
    refund_amount = str(amount) if amount else ""
    refund_value = data.get("amount")
    if refund_value:
        refund_amount = str(refund_value.get("value"))
    return {
        "id": data.get("id"),
        "status": str(data.get("status")),
        "refund_amount": refund_amount,
        "raw": data,
    }


def get_order(order_id: str) -> dict[str, Any]:
    """Retrieve a PayPal order by ID.

    Args:
        order_id: The PayPal order ID.

    Returns:
        dict with 'id', 'status', 'amount', and 'raw' keys.

    Raises:
        PayPalOrderNotFoundError: If the order does not exist.
        PayPalError: If the retrieval fails.
    """
    client = _get_client()
    try:
        status_code, data = _request(
            client, "GET", f"/v2/checkout/orders/{order_id}"
        )
    except Exception as exc:
        if "NOT_FOUND" in str(exc) or "404" in str(exc):
            raise PayPalOrderNotFoundError(
                f"PayPal order {order_id} not found"
            ) from exc
        logger.exception("PayPal get_order failed for order %s", order_id)
        raise PayPalError(
            f"Failed to retrieve PayPal order {order_id}: {exc}"
        ) from exc
    finally:
        client.close()
    if status_code == 404 or "NOT_FOUND" in str(data):
        raise PayPalOrderNotFoundError(
            f"PayPal order {order_id} not found"
        )
    if status_code != 200:
        raise PayPalError(
            f"PayPal get_order returned status {status_code}"
        )
    amount_value = ""
    amount_currency = ""
    for pu in data.get("purchase_units") or []:
        if isinstance(pu, dict):
            pu_amount = pu.get("amount")
            if pu_amount:
                amount_value = str(pu_amount.get("value"))
                amount_currency = str(pu_amount.get("currency_code"))
        break
    return {
        "id": data.get("id"),
        "status": str(data.get("status")),
        "amount": amount_value,
        "currency": amount_currency,
        "raw": data,
    }


def void_payment(order_id: str) -> dict[str, Any]:
    """Void (cancel) a PayPal order that has not been captured.

    Args:
        order_id: The PayPal order ID.

    Returns:
        dict with 'id' and 'status' keys.

    Raises:
        PayPalOrderNotFoundError: If the order does not exist.
        PayPalVoidError: If the void operation fails.
    """
    client = _get_client()
    try:
        status_code, data = _request(
            client, "POST", f"/v2/checkout/orders/{order_id}/void"
        )
    except Exception as exc:
        if "NOT_FOUND" in str(exc) or "404" in str(exc):
            raise PayPalOrderNotFoundError(
                f"PayPal order {order_id} not found"
            ) from exc
        logger.exception("PayPal void_payment failed for order %s", order_id)
        raise PayPalVoidError(
            f"Failed to void PayPal order {order_id}: {exc}"
        ) from exc
    finally:
        client.close()
    if status_code == 404 or "NOT_FOUND" in str(data):
        raise PayPalOrderNotFoundError(
            f"PayPal order {order_id} not found"
        )
    if status_code not in (200, 204):
        raise PayPalVoidError(
            f"PayPal void returned status {status_code}"
        )
    return {
        "id": order_id,
        "status": "VOIDED",
    }


__all__ = [
    "HAS_PAYPAL",
    "PayPalError",
    "PayPalOrderNotFoundError",
    "PayPalCaptureError",
    "PayPalRefundError",
    "PayPalVoidError",
    "PayPalConfigurationError",
    "is_available",
    "create_order",
    "capture_payment",
    "refund_payment",
    "get_order",
    "void_payment",
]
