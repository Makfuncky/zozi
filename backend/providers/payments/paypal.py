"""PayPal SDK access point for the provider layer.

The paypalrestsdk / checkout-sdk Python packages are external integrations.
Service-layer code must not import them directly; it should reach them through
this provider module so that all third-party payment SDK usage is centralized
behind the provider boundary.
"""

from __future__ import annotations

import logging
import os
from decimal import Decimal
from typing import Any, Optional

from providers.payments.config import (
    is_paypal_configured,
    resolve_paypal_credentials,
)

logger = logging.getLogger(__name__)

HAS_PAYPAL = False
_paypal_sdk = None
_paypal_http = None

try:
    import paypalrestsdk as _paypal_sdk  # type: ignore[import-untyped]
    HAS_PAYPAL = True
except ImportError:
    try:
        from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment, LiveEnvironment  # type: ignore[import-untyped]
        _paypal_http = PayPalHttpClient
        HAS_PAYPAL = True
    except ImportError:
        pass


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
            "PayPal SDK is not installed. Install 'paypalrestsdk' or 'paypal-checkout-sdk'."
        )
    if _paypal_sdk is not None:
        return _paypal_sdk
    raise PayPalConfigurationError("PayPal SDK client is not available.")


def _get_client() -> Any:
    """Build and return a PayPal HTTP client from environment credentials."""
    if _paypal_http is None:
        raise PayPalConfigurationError(
            "PayPal checkout SDK is not installed. Install 'paypal-checkout-sdk'."
        )
    client_id, secret, base_url = resolve_paypal_credentials()
    if not client_id or not secret:
        raise PayPalConfigurationError(
            "PAYPAL_CLIENT_ID and PAYPAL_SECRET must be set."
        )
    if "sandbox" in base_url:
        environment = SandboxEnvironment(client_id=client_id, client_secret=secret)
    else:
        environment = LiveEnvironment(client_id=client_id, client_secret=secret)
    return PayPalHttpClient(environment)


def is_available() -> bool:
    """Return True when the PayPal SDK is importable and credentials are set."""
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
        PayPalConfigurationError: If PayPal SDK or credentials are missing.
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
    try:
        request = _paypal_http.OrdersCreateRequest() if False else None
    except (AttributeError, TypeError):
        pass
    try:
        from paypalcheckoutsdk.orders import OrdersCreateRequest  # type: ignore[import-untyped]
        request = OrdersCreateRequest()
        request.prefer("return=representation")
        request.request_body(payload)
        response = client.execute(request)
    except ImportError as exc:
        raise PayPalConfigurationError(f"PayPal checkout SDK unavailable: {exc}") from exc
    except Exception as exc:
        logger.exception("PayPal create_order failed")
        raise PayPalError(f"Failed to create PayPal order: {exc}") from exc
    if response.status_code not in (200, 201):
        raise PayPalError(
            f"PayPal create_order returned status {response.status_code}"
        )
    result = response.result
    approval_url = ""
    for link in result.links or []:
        if link.rel == "approve":
            approval_url = link.href
            break
    return {
        "id": result.id,
        "status": str(result.status),
        "approval_url": approval_url,
        "raw": result.to_dict() if hasattr(result, "to_dict") else result,
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
    try:
        from paypalcheckoutsdk.orders import OrdersCaptureRequest  # type: ignore[import-untyped]
        request = OrdersCaptureRequest(order_id)
        request.prefer("return=representation")
        if amount is not None and currency:
            request.request_body({
                "amount": {
                    "currency_code": currency.upper(),
                    "value": str(amount),
                }
            })
        response = client.execute(request)
    except Exception as exc:
        if "NOT_FOUND" in str(exc) or "404" in str(exc):
            raise PayPalOrderNotFoundError(
                f"PayPal order {order_id} not found"
            ) from exc
        logger.exception("PayPal capture_payment failed for order %s", order_id)
        raise PayPalCaptureError(
            f"Failed to capture PayPal order {order_id}: {exc}"
        ) from exc
    if response.status_code not in (200, 201):
        raise PayPalCaptureError(
            f"PayPal capture returned status {response.status_code}"
        )
    result = response.result
    capture_amount = str(amount) if amount else ""
    status = str(result.status)
    for pu in result.purchase_units or []:
        if hasattr(pu, "payments") and pu.payments:
            for cap in (pu.payments.captures or []):
                status = str(cap.status)
                if hasattr(cap, "amount"):
                    capture_amount = str(cap.amount.value)
                break
    return {
        "id": result.id,
        "status": status,
        "capture_amount": capture_amount,
        "raw": result.to_dict() if hasattr(result, "to_dict") else result,
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
    try:
        from paypalcheckoutsdk.payments import CapturesRefundRequest  # type: ignore[import-untyped]
        request = CapturesRefundRequest(capture_id)
        request.prefer("return=representation")
        body: dict[str, Any] = {}
        if reason:
            body["note_to_payer"] = reason
        if amount is not None and currency:
            body["amount"] = {
                "currency_code": currency.upper(),
                "value": str(amount),
            }
        if body:
            request.request_body(body)
        response = client.execute(request)
    except Exception as exc:
        logger.exception("PayPal refund_payment failed for capture %s", capture_id)
        raise PayPalRefundError(
            f"Failed to refund PayPal capture {capture_id}: {exc}"
        ) from exc
    if response.status_code not in (200, 201):
        raise PayPalRefundError(
            f"PayPal refund returned status {response.status_code}"
        )
    result = response.result
    refund_amount = str(amount) if amount else ""
    if hasattr(result, "amount") and result.amount:
        refund_amount = str(result.amount.value)
    return {
        "id": result.id,
        "status": str(result.status),
        "refund_amount": refund_amount,
        "raw": result.to_dict() if hasattr(result, "to_dict") else result,
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
        from paypalcheckoutsdk.orders import OrdersGetRequest  # type: ignore[import-untyped]
        request = OrdersGetRequest(order_id)
        response = client.execute(request)
    except Exception as exc:
        if "NOT_FOUND" in str(exc) or "404" in str(exc):
            raise PayPalOrderNotFoundError(
                f"PayPal order {order_id} not found"
            ) from exc
        logger.exception("PayPal get_order failed for order %s", order_id)
        raise PayPalError(
            f"Failed to retrieve PayPal order {order_id}: {exc}"
        ) from exc
    if response.status_code != 200:
        raise PayPalError(
            f"PayPal get_order returned status {response.status_code}"
        )
    result = response.result
    amount_value = ""
    amount_currency = ""
    for pu in result.purchase_units or []:
        if hasattr(pu, "amount") and pu.amount:
            amount_value = str(pu.amount.value)
            amount_currency = str(pu.amount.currency_code)
        break
    return {
        "id": result.id,
        "status": str(result.status),
        "amount": amount_value,
        "currency": amount_currency,
        "raw": result.to_dict() if hasattr(result, "to_dict") else result,
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
        from paypalcheckoutsdk.orders import OrdersVoidRequest  # type: ignore[import-untyped]
        request = OrdersVoidRequest(order_id)
        response = client.execute(request)
    except Exception as exc:
        if "NOT_FOUND" in str(exc) or "404" in str(exc):
            raise PayPalOrderNotFoundError(
                f"PayPal order {order_id} not found"
            ) from exc
        logger.exception("PayPal void_payment failed for order %s", order_id)
        raise PayPalVoidError(
            f"Failed to void PayPal order {order_id}: {exc}"
        ) from exc
    if response.status_code not in (200, 204):
        raise PayPalVoidError(
            f"PayPal void returned status {response.status_code}"
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
