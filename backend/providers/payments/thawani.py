"""Payment gateway provider: thawani.

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
from infrastructure.messaging.events import PaymentConfirmedEvent, PaymentFailedEvent, PaymentRefundedEvent, EventPublisher, _event_publisher
from infrastructure.utils.config import settings
from infrastructure.utils.currency import (
    convert_from_aed,
    get_currency_context,
    money_to_minor_units_for_currency,
)

from providers.payments import payment_persistence as pp

logger = logging.getLogger(__name__)


__all__ = ['create_thawani_session', 'handle_thawani_webhook', 'confirm_thawani_payment', '_resolve_thawani_secret_key', '_resolve_thawani_publishable_key', '_resolve_thawani_api_base_url', '_resolve_thawani_webhook_secret', '_thawani_configured', '_thawani_checkout_enabled']

async def create_thawani_session(body: ThawaniCheckoutRequest, current_user: dict, db: Session) -> dict:
    """Create a Thawani hosted-checkout session and return the redirect URL."""
    configured, secret_key, publishable_key, api_base_url = _thawani_configured(db)
    if not configured:
        raise HTTPException(status_code=503, detail="Thawani Pay is not configured")
    if not _thawani_checkout_enabled(db):
        raise HTTPException(status_code=409, detail="Thawani Pay is currently disabled")

    order = _get_user_order(body.order_id, current_user, db)
    if _normalized_payment_method(order) != THAWANI_PAYMENT_METHOD:
        raise HTTPException(status_code=409, detail="This order is not configured for Thawani payment")
    if order.paid_at is not None:
        raise HTTPException(status_code=409, detail="Order is already paid")

    # Convert amount to OMR (from base AED) then to baisa (×1000), must be int
    charge_total = _order_charge_total_amount(order)
    omr_amount = convert_from_aed(charge_total, "OMR")
    unit_amount_baisa = max(1, int(round(float(omr_amount) * 1000)))

    is_uat = "uatcheckout" in api_base_url
    pay_base = DEFAULT_THAWANI_UAT_PAY_BASE if is_uat else DEFAULT_THAWANI_LIVE_PAY_BASE

    payload = {
        "client_reference_id": str(order.id),
        "mode": "payment",
        "products": [
            {
                "name": body.description or f"ZOZI Order #{order.id}",
                "unit_amount": unit_amount_baisa,
                "quantity": 1,
            }
        ],
        "success_url": body.success_url,
        "cancel_url": body.cancel_url,
        "metadata": {
            "Customer name": f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip(),
            "order id": str(order.id),
        },
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{api_base_url}/checkout/session",
                headers={
                    "thawani-api-key": secret_key,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        data = resp.json()
        if resp.status_code not in (200, 201) or not data.get("success"):
            logger.error("Thawani session creation failed (%s): %s", resp.status_code, data)
            raise HTTPException(
                status_code=400,
                detail=str(data.get("description") or "Thawani checkout session creation failed"),
            )

        session_id = str((data.get("data") or {}).get("session_id") or "").strip()
        if not session_id:
            raise HTTPException(status_code=400, detail="Thawani did not return a session_id")

        checkout_url = f"{pay_base}/pay/{session_id}?key={publishable_key}"

        setattr(order, "payment_intent_id", session_id)
        pp.commit(db)

        return {
            "session_id": session_id,
            "checkout_url": checkout_url,
            "currency": "OMR",
            "display_amount": float(omr_amount),
            "unit_amount_baisa": unit_amount_baisa,
        }
    except HTTPException as e:
        logger.exception("create_thawani_session_failed", error=str(e))
        raise
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:
        logger.error("Thawani session creation error: %s", exc)
        raise HTTPException(status_code=500, detail="Thawani payment service error")


async def handle_thawani_webhook(request: Request, db: Session) -> dict:
    """Verify and process Thawani webhook event notifications."""
    import json as _json

    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8", errors="replace")

    # ── Signature verification ────────────────────────────────────────────────
    thawani_timestamp = request.headers.get("thawani-timestamp", "")
    thawani_signature = request.headers.get("thawani-signature", "")

    webhook_secret = _resolve_thawani_webhook_secret(db)
    if webhook_secret:
        if not thawani_timestamp or not thawani_signature:
            logger.warning("thawani_webhook: missing signature headers")
            raise HTTPException(status_code=400, detail="Missing Thawani webhook signature headers")
        expected_sig = hmac.new(
            webhook_secret.encode("utf-8"),
            f"{body_str}-{thawani_timestamp}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected_sig, thawani_signature):
            logger.warning("thawani_webhook: invalid signature")
            raise HTTPException(status_code=400, detail="Invalid Thawani webhook signature")
    else:
        logger.warning(
            "thawani_webhook: THAWANI_WEBHOOK_SECRET is not configured; "
            "signature verification is skipped. Set thawani_webhook_secret in production."
        )

    try:
        event_data = _json.loads(body_bytes)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
        logger.exception("handle_thawani_webhook_failed", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid Thawani webhook payload")

    event_type = str(event_data.get("type") or event_data.get("event_type") or "").strip()
    data = event_data.get("data") or {}
    if not isinstance(data, dict):
        data = {}

    # ── Idempotency key: use invoice or session_id + event type ──────────────
    invoice_id = str(data.get("invoice") or data.get("id") or "").strip()
    session_id_field = str(data.get("session_id") or data.get("checkout_session_id") or "").strip()
    idempotency_key = f"thawani:{event_type}:{invoice_id or session_id_field}"

    if invoice_id or session_id_field:
        existing = db.query(ProcessedWebhookEvent).filter(
            ProcessedWebhookEvent.event_id == idempotency_key,
            ProcessedWebhookEvent.processor == THAWANI_PAYMENT_METHOD,
        ).first()
        if existing:
            return {"status": "duplicate"}

    # ── Resolve order ─────────────────────────────────────────────────────────
    order = None

    # For checkout.* events: client_reference_id is our order ID
    client_ref = str(data.get("client_reference_id") or "").strip()
    if client_ref and client_ref.isdigit():
        order = db.query(Order).filter(Order.id == int(client_ref)).first()

    # For payment.* events: checkout_invoice links back; try payment_intent_id match
    if order is None:
        checkout_invoice = str(data.get("checkout_invoice") or "").strip()
        if checkout_invoice:
            order = db.query(Order).filter(Order.payment_intent_id == checkout_invoice).first()

    # Fallback: match by session_id stored as payment_intent_id
    if order is None and session_id_field:
        order = db.query(Order).filter(Order.payment_intent_id == session_id_field).first()

    # ── Process event ─────────────────────────────────────────────────────────
    if event_type in ("checkout.session.completed", "session.completed"):
        payment_status = str(data.get("payment_status") or "").strip().lower()
        if payment_status == "paid" and order:
            if order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:
                _apply_successful_payment(
                    order,
                    f"Order #{order.id} payment via Thawani Pay was successful.",
                    db,
                )
                pp.commit(db)

    elif event_type in ("payment.succeeded",):
        if order and order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:
            _apply_successful_payment(
                order,
                f"Order #{order.id} Thawani webhook: payment succeeded.",
                db,
            )
            pp.commit(db)

    elif event_type in ("payment.failed",):
        if order and order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:
            setattr(order, "status", "failed")
            pp.add(db, 
                Notification(
                    user_id=order.user_id,
                    type="order_update",
                    title="Payment Failed",
                    message=f"Order #{order.id} Thawani payment failed.",
                    link=f"/orders/{order.id}",
                )
            )
            pp.commit(db)
            try:
                event = PaymentFailedEvent.create(
                    order_id=order.id,
                    user_id=order.user_id,
                    provider="thawani",
                    message=f"Order #{order.id} Thawani payment failed.",
                )
                _event_publisher.publish(event)
            except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
                logger.exception("Thawani webhook: failed to publish PaymentFailedEvent for order %s", order.id)

    else:
        logger.debug("Unhandled Thawani webhook event: %s", event_type)

    if invoice_id or session_id_field:
        pp.add(db, ProcessedWebhookEvent(event_id=idempotency_key, processor=THAWANI_PAYMENT_METHOD))
        pp.commit(db)

    return {"status": "ok"}


async def confirm_thawani_payment(body: ConfirmThawaniPaymentRequest, current_user: dict, db: Session) -> dict:
    """Poll Thawani session status after the customer returns from the hosted checkout page.

    Called by the frontend when the customer lands back on our success URL.  The
    function re-queries Thawani's retrieve-session endpoint to get the authoritative
    payment_status and — if the status is 'paid' — applies the successful payment
    (idempotent: safe to call multiple times).

    Returns a dict with keys:
        status  "confirmed" | "pending" | "failed"
        order_id, order_status, session_id, paid_at
    """
    order = _get_user_order(body.order_id, current_user, db)

    # Already confirmed — return immediately
    if order.paid_at is not None:
        return {
            "status": "confirmed",
            "order_id": order.id,
            "order_status": order.status,
            "session_id": str(getattr(order, "payment_intent_id", "") or "").strip(),
            "paid_at": order.paid_at,
        }

    session_id = str(getattr(order, "payment_intent_id", "") or "").strip()
    if not session_id:
        return {
            "status": "pending",
            "order_id": order.id,
            "order_status": order.status,
            "session_id": None,
            "paid_at": None,
        }

    configured, secret_key, _pub_key, api_base_url = _thawani_configured(db)
    if not configured:
        return {
            "status": "pending",
            "order_id": order.id,
            "order_status": order.status,
            "session_id": session_id,
            "paid_at": None,
        }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{api_base_url}/checkout/session/{session_id}",
                headers={"thawani-api-key": secret_key},
            )
        data = resp.json()
        session_data = data.get("data") or {}
        if not isinstance(session_data, dict):
            session_data = {}
        payment_status = str(session_data.get("payment_status") or "").strip().lower()
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:
        logger.error("Thawani confirm: session retrieve error: %s", exc)
        return {
            "status": "pending",
            "order_id": order.id,
            "order_status": order.status,
            "session_id": session_id,
            "paid_at": None,
        }

    if payment_status == "paid":
        if order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:
            _apply_successful_payment(
                order,
                f"Order #{order.id} Thawani confirm: payment_status=paid.",
                db,
            )
            pp.commit(db)
        return {
            "status": "confirmed",
            "order_id": order.id,
            "order_status": order.status,
            "session_id": session_id,
            "paid_at": order.paid_at,
        }

    if payment_status in ("cancelled", "failed", "refunded"):
        if order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:
            setattr(order, "status", "failed")
            pp.commit(db)
        return {
            "status": "failed",
            "order_id": order.id,
            "order_status": order.status,
            "session_id": session_id,
            "paid_at": None,
        }

    return {
        "status": "pending",
        "order_id": order.id,
        "order_status": order.status,
        "session_id": session_id,
        "paid_at": None,
    }


def _resolve_thawani_secret_key(db: Session | None = None) -> str:
    if db is not None:
        record = _get_gateway_connection_record(db, THAWANI_PAYMENT_METHOD)
        if record:
            raw = decrypt_secret(cast(str | None, getattr(record, "secret_key", None)))
            if raw:
                return raw.strip()
    return str(getattr(settings, "thawani_secret_key", "") or "").strip()


def _resolve_thawani_publishable_key(db: Session | None = None) -> str:
    if db is not None:
        record = _get_gateway_connection_record(db, THAWANI_PAYMENT_METHOD)
        if record:
            raw = decrypt_secret(cast(str | None, getattr(record, "public_key", None)))
            if raw:
                return raw.strip()
    return str(getattr(settings, "thawani_publishable_key", "") or "").strip()


def _resolve_thawani_api_base_url(db: Session | None = None) -> str:
    if db is not None:
        record = _get_gateway_connection_record(db, THAWANI_PAYMENT_METHOD)
        configured_url = _optional_text(getattr(record, "api_base_url", None)) if record else None
        if configured_url:
            return configured_url.rstrip("/")
    return DEFAULT_THAWANI_UAT_URL


def _resolve_thawani_webhook_secret(db: Session | None = None) -> str:
    if db is not None:
        record = _get_gateway_connection_record(db, THAWANI_PAYMENT_METHOD)
        if record:
            raw = decrypt_secret(cast(str | None, getattr(record, "webhook_secret", None)))
            if raw:
                return raw.strip()
    return str(getattr(settings, "thawani_webhook_secret", "") or "").strip()


def _thawani_configured(db: Session | None = None) -> tuple[bool, str, str, str]:
    """Return (configured, secret_key, publishable_key, api_base_url)."""
    secret_key = _resolve_thawani_secret_key(db)
    publishable_key = _resolve_thawani_publishable_key(db)
    api_base_url = _resolve_thawani_api_base_url(db)
    return bool(secret_key and publishable_key), secret_key, publishable_key, api_base_url


def _thawani_checkout_enabled(db: Session) -> bool:
    configured, _, _, _ = _thawani_configured(db)
    gateway = _serialize_gateway_connection(THAWANI_PAYMENT_METHOD, db, _get_gateway_connection_record(db, THAWANI_PAYMENT_METHOD))
    return configured and gateway.is_enabled and gateway.supports_customer_checkout and gateway.adapter_supported

from providers.payments._common import *  # noqa: E402,F401,F403
from providers.payments._order import *   # noqa: E402,F401,F403
from providers.payments.config import *    # noqa: E402,F401,F403
from providers.payments.webhooks import * # noqa: E402,F401,F403
from providers.payments.stripe import *    # noqa: E402,F401,F403
from providers.payments.tap import *       # noqa: E402,F401,F403
from providers.payments.paytabs import *   # noqa: E402,F401,F403
from providers.payments.paypal import *    # noqa: E402,F401,F403
import structlog
logger = structlog.get_logger(__name__)
from providers.payments.thawani import *   # noqa: E402,F401,F403
from providers.payments.generic import *   # noqa: E402,F401,F403

