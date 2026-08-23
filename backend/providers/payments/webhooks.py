"""Payment gateway provider: webhooks.

Relocated from controllers/payments_controller.py.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import stripe
import httpx
import logging
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import Any, Literal, Optional, cast
from urllib.parse import parse_qs

from fastapi import HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from domains.catalog.models.products import Product
from domains.comms.models.communication import Notification
from domains.country.models.countries import CountryConfig
from domains.finance.models.finance import TransactionLedger
from domains.governance.models.admin import PaymentProviderConfig
from domains.governance.models.admin import ProcessedWebhookEvent
from domains.orders.models.orders import Order
from domains.orders.models.orders import OrderItem
from domains.catalog.models.promotions import Coupon
from domains.finance.models.payments import Payment
from domains.finance.models.payments import PaymentGatewayConnection
from infrastructure.messaging.events import PaymentConfirmedEvent, EventPublisher, _event_publisher
from infrastructure.utils.config import settings
from infrastructure.utils.currency import (
    convert_from_aed,
    get_currency_context,
    money_to_minor_units_for_currency,
)

logger = logging.getLogger(__name__)


__all__ = ['_verify_paytabs_signature', '_verify_tap_signature', '_generic_verify_payment']

def _verify_paytabs_signature(payload: bytes, signature: str, webhook_secret: str) -> bool:
    if not webhook_secret or not signature:
        return False
    expected = hmac.new(
        webhook_secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


def _verify_tap_signature(raw_body: bytes, sig_header: str, db: Session | None = None) -> bool:
    """
    Verify an incoming Tap webhook request.

    Tap signs each webhook POST with an HMAC-SHA256 digest calculated over the
    raw request body, using TAP_WEBHOOK_SECRET as the key.  The digest is
    delivered in the 'hashstring' header (Tap docs, 2024 API reference).

    Returns True when the signature is valid, False otherwise.
    If TAP_WEBHOOK_SECRET is not configured the function returns False so that
    the caller can reject the request with an appropriate HTTP error.
    """
    secret = _resolve_tap_webhook_secret(db)
    if not secret:
        return False
    expected = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, sig_header)


def _generic_verify_payment(
    extra: dict[str, Any],
    record: "PaymentGatewayConnection",
    order: Order,
    reference: str,
    db: Session,
) -> str:
    """Poll a configured provider verify endpoint and return 'success' | 'failed' | 'unknown'."""
    verify_url = _optional_text(extra.get("verify_url"))
    if not verify_url:
        return "unknown"
    normalized_code = _normalize_gateway_code(getattr(record, "provider_code", ""))
    callback_url = f"{_resolve_gateway_callback_base(db, normalized_code)}/payments/generic/{normalized_code}/callback"
    ctx: dict[str, Any] = {
        "order_id": order.id,
        "reference": reference or str(getattr(order, "payment_intent_id", "") or ""),
        "transaction_ref": reference or str(getattr(order, "payment_intent_id", "") or ""),
        "amount": float(_order_charge_total_amount(order)),
        "currency": str(getattr(order, "shipping_country", "") or ""),
        "callback_url": callback_url,
        "customer_email": getattr(order, "customer_email", None) or "",
        "customer_name": getattr(order, "customer_name", None) or "",
    }
    url = _fill_gateway_template(verify_url, ctx)
    method = str(extra.get("verify_method", "GET")).upper()
    headers: dict[str, str] = {"accept": "application/json"}
    auth_header = _optional_text(extra.get("verify_auth_header"))
    if auth_header:
        headers["Authorization"] = _fill_gateway_template(
            auth_header, {**ctx, "secret_key": _optional_text(getattr(record, "secret_key", None)) or ""}
        )
    try:
        with httpx.Client(timeout=20) as client:
            resp = client.request(method, url, headers=headers)
            if resp.status_code >= 400:
                logger.warning("generic verify %s failed: %s", normalized_code, resp.status_code)
                return "unknown"
            data = resp.json()
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:
        logger.error("generic verify call error: %s", exc)
        return "unknown"

    status_field = str(extra.get("verify_status_field", "status") or "status")
    success_values = [str(v).lower() for v in (extra.get("verify_success_values") or list(_GENERIC_DEFAULT_SUCCESS_VALUES))]
    fail_values = [str(v).lower() for v in (extra.get("verify_failed_values") or ["failed", "declined", "error", "cancelled"])]
    resolved = str(data.get(status_field) or "").lower()
    if resolved in success_values:
        return "success"
    if resolved in fail_values:
        return "failed"
    return "unknown"

from providers.payments._common import *  # noqa: E402,F401,F403
from providers.payments._order import *   # noqa: E402,F401,F403
from providers.payments.config import *    # noqa: E402,F401,F403
from providers.payments.webhooks import * # noqa: E402,F401,F403
from providers.payments.stripe import *    # noqa: E402,F401,F403
from providers.payments.tap import *       # noqa: E402,F401,F403
from providers.payments.paytabs import *   # noqa: E402,F401,F403
from providers.payments.paypal import *    # noqa: E402,F401,F403
from providers.payments.thawani import *   # noqa: E402,F401,F403
from providers.payments.generic import *   # noqa: E402,F401,F403
import structlog
logger = structlog.get_logger(__name__)

