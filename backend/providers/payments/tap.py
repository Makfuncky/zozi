"""Tap Payments SDK access point for the provider layer.

Tap Payments (formerly Tap) is an HTTP-based payment gateway operating in the
Middle East and North Africa. This module wraps their REST API (token-based
authentication, JSON payloads) behind a provider boundary.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Optional

import requests

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


class TapError(Exception):
    """Base exception for Tap provider operations."""


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
        response = requests.post(
            f"{api_base}/charges",
            json=payload,
            headers=_get_headers(),
            timeout=_TAP_DEFAULT_TIMEOUT,
        )
    except requests.RequestException as exc:
        logger.exception("Tap create_charge request failed")
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
        response = requests.get(
            f"{api_base}/charges/{charge_id}",
            headers=_get_headers(),
            timeout=_TAP_DEFAULT_TIMEOUT,
        )
    except requests.RequestException as exc:
        logger.exception("Tap get_charge request failed for %s", charge_id)
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
    try:
        response = requests.post(
            f"{api_base}/charges/{charge_id}/refunds",
            json=payload,
            headers=_get_headers(),
            timeout=_TAP_DEFAULT_TIMEOUT,
        )
    except requests.RequestException as exc:
        logger.exception(
            "Tap refund_charge request failed for %s", charge_id
        )
        raise TapRefundError(
            f"Tap API request failed: {exc}"
        ) from exc
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
