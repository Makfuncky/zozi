"""PayTabs SDK access point for the provider layer.

PayTabs is an HTTP-based payment gateway. This module wraps their REST API
(server-key authentication, JSON payloads) behind a provider boundary so that
service-layer code never imports `requests` directly for PayTabs calls.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Optional

import requests

from providers.payments.config import (
    is_paytabs_configured,
    resolve_paytabs_api_base_url,
    resolve_paytabs_callback_url,
    resolve_paytabs_profile_id,
    resolve_paytabs_server_key,
)
from providers.payments.webhooks import _verify_paytabs_signature

logger = logging.getLogger(__name__)

HAS_PAYTABS = True
_PAYTABS_DEFAULT_TIMEOUT = 30


class PayTabsError(Exception):
    """Base exception for PayTabs provider operations."""


class PayTabsPaymentNotFoundError(PayTabsError):
    """Raised when a PayTabs payment reference does not exist."""


class PayTabsRefundError(PayTabsError):
    """Raised when a PayTabs refund operation fails."""


class PayTabsConfigurationError(PayTabsError):
    """Raised when PayTabs credentials are missing or invalid."""


def _get_headers() -> dict[str, str]:
    """Build authenticated headers for PayTabs API calls."""
    server_key = resolve_paytabs_server_key()
    if not server_key:
        raise PayTabsConfigurationError(
            "PAYTABS_SERVER_KEY must be set."
        )
    return {
        "Content-Type": "application/json",
        "Authorization": server_key,
    }


def is_available() -> bool:
    """Return True when PayTabs credentials are configured."""
    return is_paytabs_configured()


def create_payment_page(
    amount: Decimal,
    currency: str,
    *,
    customer_name: str,
    customer_email: str,
    customer_phone: str = "",
    order_id: str = "",
    description: str = "",
    callback_url: str = "",
    return_url: str = "",
    metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Create a PayTabs payment page (hosted checkout).

    Args:
        amount: The payment total.
        currency: ISO 4217 currency code.
        customer_name: Full name of the customer.
        customer_email: Customer email address.
        customer_phone: Customer phone number.
        order_id: Merchant-side order reference.
        description: Payment description.
        callback_url: Server-to-server callback URL.
        return_url: Customer redirect URL after payment.
        metadata: Additional fields merged into the request payload.

    Returns:
        dict with 'payment_url', 'transaction_id', and 'raw' keys.

    Raises:
        PayTabsConfigurationError: If credentials are missing.
        PayTabsError: If page creation fails.
    """
    api_base = resolve_paytabs_api_base_url()
    profile_id = resolve_paytabs_profile_id()
    resolved_callback = callback_url or resolve_paytabs_callback_url()
    payload: dict[str, Any] = {
        "profile_id": profile_id,
        "tran_type": "sale",
        "tran_class": "ecom",
        "cart_id": order_id,
        "cart_description": description or f"Payment for order {order_id}",
        "cart_currency": currency.upper(),
        "cart_amount": str(amount),
        "customer_details": {
            "name": customer_name,
            "email": customer_email,
            "phone": customer_phone or "",
            "street1": "",
            "city": "",
            "state": "",
            "country": "",
            "zip": "",
        },
        "callback": resolved_callback,
        "return": return_url or resolved_callback,
    }
    if metadata:
        payload["framed"] = metadata.get("framed", False)
        payload["metadata"] = metadata
    try:
        response = requests.post(
            f"{api_base}/payment/request",
            json=payload,
            headers=_get_headers(),
            timeout=_PAYTABS_DEFAULT_TIMEOUT,
        )
    except requests.RequestException as exc:
        logger.exception("PayTabs create_payment_page request failed")
        raise PayTabsError(
            f"PayTabs API request failed: {exc}"
        ) from exc
    if response.status_code != 200:
        raise PayTabsError(
            f"PayTabs create_payment_page returned status {response.status_code}: {response.text}"
        )
    data = response.json()
    if not data.get("payment_url") and not data.get("tran_ref"):
        raise PayTabsError(
            f"PayTabs create_payment_page unexpected response: {data}"
        )
    return {
        "payment_url": data.get("payment_url", ""),
        "transaction_id": data.get("tran_ref", ""),
        "redirect_url": data.get("redirect_url", ""),
        "raw": data,
    }


def get_payment_status(transaction_ref: str) -> dict[str, Any]:
    """Retrieve the status of a PayTabs payment.

    Args:
        transaction_ref: The PayTabs transaction reference.

    Returns:
        dict with 'transaction_id', 'status', 'amount', 'currency', and 'raw' keys.

    Raises:
        PayTabsPaymentNotFoundError: If the transaction does not exist.
        PayTabsError: If the status query fails.
    """
    api_base = resolve_paytabs_api_base_url()
    profile_id = resolve_paytabs_profile_id()
    payload: dict[str, Any] = {
        "profile_id": profile_id,
        "tran_ref": transaction_ref,
    }
    try:
        response = requests.post(
            f"{api_base}/payment/query",
            json=payload,
            headers=_get_headers(),
            timeout=_PAYTABS_DEFAULT_TIMEOUT,
        )
    except requests.RequestException as exc:
        logger.exception(
            "PayTabs get_payment_status request failed for %s", transaction_ref
        )
        raise PayTabsError(
            f"PayTabs API request failed: {exc}"
        ) from exc
    if response.status_code != 200:
        raise PayTabsError(
            f"PayTabs get_payment_status returned status {response.status_code}"
        )
    data = response.json()
    if data.get("code") == 404 or "not found" in str(data.get("message", "")).lower():
        raise PayTabsPaymentNotFoundError(
            f"PayTabs transaction {transaction_ref} not found"
        )
    return {
        "transaction_id": data.get("tran_ref", transaction_ref),
        "status": data.get("payment_result", {}).get("response_status", ""),
        "amount": str(data.get("cart_amount", "")),
        "currency": data.get("cart_currency", ""),
        "reference": data.get("tran_ref", ""),
        "raw": data,
    }


def refund(
    transaction_ref: str,
    *,
    amount: Optional[Decimal] = None,
    currency: Optional[str] = None,
    reason: str = "",
) -> dict[str, Any]:
    """Refund a PayTabs payment.

    Args:
        transaction_ref: The PayTabs transaction reference.
        amount: Optional partial refund amount (full refund if omitted).
        currency: Currency code (required if amount is provided).
        reason: Reason for the refund.

    Returns:
        dict with 'refund_id', 'status', and 'raw' keys.

    Raises:
        PayTabsPaymentNotFoundError: If the transaction does not exist.
        PayTabsRefundError: If the refund operation fails.
    """
    api_base = resolve_paytabs_api_base_url()
    profile_id = resolve_paytabs_profile_id()
    payload: dict[str, Any] = {
        "profile_id": profile_id,
        "tran_type": "refund",
        "tran_class": "ecom",
        "tran_ref": transaction_ref,
        "cart_description": reason or "Refund",
        "cart_currency": currency or "",
        "cart_amount": str(amount) if amount else "0",
    }
    if amount and currency:
        payload["cart_amount"] = str(amount)
    try:
        response = requests.post(
            f"{api_base}/payment/request",
            json=payload,
            headers=_get_headers(),
            timeout=_PAYTABS_DEFAULT_TIMEOUT,
        )
    except requests.RequestException as exc:
        logger.exception(
            "PayTabs refund request failed for %s", transaction_ref
        )
        raise PayTabsRefundError(
            f"PayTabs API request failed: {exc}"
        ) from exc
    if response.status_code != 200:
        raise PayTabsRefundError(
            f"PayTabs refund returned status {response.status_code}"
        )
    data = response.json()
    if data.get("code") == 404 or "not found" in str(data.get("message", "")).lower():
        raise PayTabsPaymentNotFoundError(
            f"PayTabs transaction {transaction_ref} not found"
        )
    return {
        "refund_id": data.get("tran_ref", ""),
        "status": data.get("payment_result", {}).get("response_status", ""),
        "amount": str(data.get("cart_amount", "")),
        "raw": data,
    }


def verify_webhook(
    raw_body: bytes,
    signature_header: str,
    webhook_secret: str,
) -> bool:
    """Verify an incoming PayTabs webhook signature.

    Args:
        raw_body: The raw request body bytes.
        signature_header: The signature from the webhook request header.
        webhook_secret: The shared webhook secret.

    Returns:
        True if the signature is valid.
    """
    return _verify_paytabs_signature(raw_body, signature_header, webhook_secret)


__all__ = [
    "HAS_PAYTABS",
    "PayTabsError",
    "PayTabsPaymentNotFoundError",
    "PayTabsRefundError",
    "PayTabsConfigurationError",
    "is_available",
    "create_payment_page",
    "get_payment_status",
    "refund",
    "verify_webhook",
]
