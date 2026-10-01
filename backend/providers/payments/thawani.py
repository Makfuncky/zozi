"""Thawani Pay SDK access point for the provider layer.

Thawani Pay is an HTTP-based payment gateway operating in Oman and the wider
GCC region. This module wraps their REST API (token-based authentication, JSON
payloads) behind a provider boundary.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Optional

import requests

from providers.payments.config import (
    is_thawani_configured,
    resolve_thawani_api_base_url,
    resolve_thawani_publishable_key,
    resolve_thawani_secret_key,
    resolve_thawani_webhook_secret,
)

logger = logging.getLogger(__name__)

HAS_THAWANI = True
_THAWANI_DEFAULT_TIMEOUT = 30


class ThawaniError(Exception):
    """Base exception for Thawani provider operations."""


class ThawaniSessionNotFoundError(ThawaniError):
    """Raised when a Thawani session does not exist."""


class ThawaniRefundError(ThawaniError):
    """Raised when a Thawani refund operation fails."""


class ThawaniConfigurationError(ThawaniError):
    """Raised when Thawani credentials are missing or invalid."""


def _get_headers() -> dict[str, str]:
    """Build authenticated headers for Thawani API calls."""
    secret_key = resolve_thawani_secret_key()
    if not secret_key:
        raise ThawaniConfigurationError("THAWANI_SECRET_KEY must be set.")
    return {
        "Content-Type": "application/json",
        "Thawani-Api-Key": secret_key,
    }


def is_available() -> bool:
    """Return True when Thawani credentials are configured."""
    return is_thawani_configured()


def create_session(
    amount: Decimal,
    currency: str,
    *,
    customer_name: str = "",
    customer_email: str = "",
    customer_phone: str = "",
    order_id: str = "",
    description: str = "",
    success_url: str = "",
    cancel_url: str = "",
    metadata: Optional[dict[str, Any]] = None,
    products: Optional[list[dict[str, Any]]] = None,
    save_card: bool = False,
) -> dict[str, Any]:
    """Create a Thawani payment session.

    Thawani's session API returns a session ID and a checkout URL the customer
    is redirected to.

    Args:
        amount: The session total (Thawani expects major currency units).
        currency: ISO 4217 currency code (e.g. 'OMR', 'SAR', 'AED').
        customer_name: Full name of the customer.
        customer_email: Customer email address.
        customer_phone: Customer phone number.
        order_id: Merchant-side order reference.
        description: Session description.
        success_url: URL to redirect after successful payment.
        cancel_url: URL to redirect on cancellation.
        metadata: Additional fields merged into the request payload.
        products: Line items to display on the checkout page.
        save_card: Whether to allow card tokenization.

    Returns:
        dict with 'session_id', 'checkout_url', and 'raw' keys.

    Raises:
        ThawaniConfigurationError: If credentials are missing.
        ThawaniError: If session creation fails.
    """
    api_base = resolve_thawani_api_base_url()
    publishable_key = resolve_thawani_publishable_key()
    payload: dict[str, Any] = {
        "client_reference_id": order_id,
        "mode": "payment",
        "products": products or [
            {
                "name": description or f"Order {order_id}",
                "quantity": 1,
                "unit_amount": int(amount * 1000),
            }
        ],
        "success_url": success_url,
        "cancel_url": cancel_url,
        "metadata": {
            "order_id": order_id,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "customer_phone": customer_phone,
        },
        "save_card_on_success": save_card,
    }
    if metadata:
        payload["metadata"].update(metadata)
    try:
        response = requests.post(
            f"{api_base}/checkout/session",
            json=payload,
            headers=_get_headers(),
            timeout=_THAWANI_DEFAULT_TIMEOUT,
        )
    except requests.RequestException as exc:
        logger.exception("Thawani create_session request failed")
        raise ThawaniError(
            f"Thawani API request failed: {exc}"
        ) from exc
    if response.status_code not in (200, 201):
        raise ThawaniError(
            f"Thawani create_session returned status {response.status_code}: {response.text}"
        )
    data = response.json()
    session_id = data.get("data", {}).get("session_id", "")
    checkout_url = ""
    if session_id and publishable_key:
        checkout_url = f"https://checkout.thawani.om/pay/{session_id}?key={publishable_key}"
    return {
        "session_id": session_id,
        "checkout_url": checkout_url,
        "status": data.get("status", ""),
        "raw": data,
    }


def get_session(session_id: str) -> dict[str, Any]:
    """Retrieve a Thawani payment session by ID.

    Args:
        session_id: The Thawani session ID.

    Returns:
        dict with 'session_id', 'status', 'amount', 'currency', and 'raw' keys.

    Raises:
        ThawaniSessionNotFoundError: If the session does not exist.
        ThawaniError: If the retrieval fails.
    """
    api_base = resolve_thawani_api_base_url()
    try:
        response = requests.get(
            f"{api_base}/checkout/session/{session_id}",
            headers=_get_headers(),
            timeout=_THAWANI_DEFAULT_TIMEOUT,
        )
    except requests.RequestException as exc:
        logger.exception(
            "Thawani get_session request failed for %s", session_id
        )
        raise ThawaniError(
            f"Thawani API request failed: {exc}"
        ) from exc
    if response.status_code == 404:
        raise ThawaniSessionNotFoundError(
            f"Thawani session {session_id} not found"
        )
    if response.status_code != 200:
        raise ThawaniError(
            f"Thawani get_session returned status {response.status_code}"
        )
    data = response.json()
    session_data = data.get("data", {})
    return {
        "session_id": session_id,
        "status": session_data.get("payment_status", ""),
        "amount": str(session_data.get("total_amount", "")),
        "currency": session_data.get("currency", ""),
        "customer_key": session_data.get("customer_key", ""),
        "raw": data,
    }


def refund_session(
    session_id: str,
    *,
    amount: Optional[Decimal] = None,
    reason: str = "",
    metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Refund a Thawani payment session.

    Args:
        session_id: The Thawani session ID to refund.
        amount: Optional partial refund amount (full refund if omitted).
        reason: Reason for the refund.
        metadata: Additional fields merged into the request payload.

    Returns:
        dict with 'refund_id', 'status', and 'raw' keys.

    Raises:
        ThawaniSessionNotFoundError: If the session does not exist.
        ThawaniRefundError: If the refund operation fails.
    """
    api_base = resolve_thawani_api_base_url()
    payload: dict[str, Any] = {
        "reason": reason or "Refund",
    }
    if amount is not None:
        payload["refund_amount"] = int(amount * 1000)
    if metadata:
        payload["metadata"] = metadata
    try:
        response = requests.post(
            f"{api_base}/checkout/session/{session_id}/refund",
            json=payload,
            headers=_get_headers(),
            timeout=_THAWANI_DEFAULT_TIMEOUT,
        )
    except requests.RequestException as exc:
        logger.exception(
            "Thawani refund_session request failed for %s", session_id
        )
        raise ThawaniRefundError(
            f"Thawani API request failed: {exc}"
        ) from exc
    if response.status_code == 404:
        raise ThawaniSessionNotFoundError(
            f"Thawani session {session_id} not found"
        )
    if response.status_code not in (200, 201):
        raise ThawaniRefundError(
            f"Thawani refund returned status {response.status_code}: {response.text}"
        )
    data = response.json()
    return {
        "refund_id": data.get("data", {}).get("refund_id", ""),
        "status": data.get("status", ""),
        "raw": data,
    }


def verify_webhook(
    raw_body: bytes,
    signature_header: str,
    webhook_secret: str,
) -> bool:
    """Verify an incoming Thawani webhook signature.

    Thawani signs webhooks with an HMAC-SHA256 signature delivered in the
    'thawani-signature' header.

    Args:
        raw_body: The raw request body bytes.
        signature_header: The signature header value.
        webhook_secret: The shared THAWANI_WEBHOOK_SECRET.

    Returns:
        True if the signature is valid.
    """
    import hashlib
    import hmac
    if not webhook_secret or not signature_header:
        return False
    expected = hmac.new(
        webhook_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


__all__ = [
    "HAS_THAWANI",
    "ThawaniError",
    "ThawaniSessionNotFoundError",
    "ThawaniRefundError",
    "ThawaniConfigurationError",
    "is_available",
    "create_session",
    "get_session",
    "refund_session",
    "verify_webhook",
]
