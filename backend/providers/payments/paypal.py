"""Payment gateway provider: paypal.

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
from domains.payments.models.payments import Coupon
from domains.payments.models.payments import Payment
from domains.payments.models.payments import PaymentGatewayConnection
from infrastructure.messaging.events import PaymentConfirmedEvent, PaymentFailedEvent, PaymentRefundedEvent, EventPublisher, _event_publisher
from infrastructure.utils.config import settings
from infrastructure.utils.currency import (
    convert_from_aed,
    get_currency_context,
    money_to_minor_units_for_currency,
)

from providers.payments import payment_persistence as pp

logger = logging.getLogger(__name__)


__all__ = ['create_paypal_order', 'capture_paypal_order', 'handle_paypal_webhook', '_paypal_get_access_token', '_paypal_configured']

async def create_paypal_order(body: PayPalOrderRequest, current_user: dict, db: Session) -> dict:
    """Create a PayPal Orders API v2 order and return the approval URL."""
    configured, client_id, secret, base_url = _paypal_configured(db)
    if not configured:
        raise HTTPException(status_code=503, detail="PayPal not configured")
    if not _paypal_gateway_enabled(db):
        raise HTTPException(status_code=409, detail="PayPal payments are currently disabled")

    order = _get_user_order(body.order_id, current_user, db)
    if _normalized_payment_method(order) != "paypal":
        raise HTTPException(status_code=409, detail="This order is not configured for PayPal payment")
    if order.paid_at is not None:
        raise HTTPException(status_code=409, detail="Order is already paid")

    currency_code = _resolved_payment_currency(body.currency, body.country)
    charge_total = _order_charge_total_amount(order)
    converted_total = convert_from_aed(charge_total, currency_code)

    try:
        access_token = await _paypal_get_access_token(cast(str, client_id), cast(str, secret), base_url)

        payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": str(order.id),
                    "custom_id": str(order.id),
                    "description": body.description or f"ZOZI Order #{order.id}",
                    "amount": {
                        "currency_code": currency_code,
                        "value": f"{converted_total:.2f}",
                    },
                }
            ],
            "application_context": {
                "brand_name": "ZOZI",
                "landing_page": "LOGIN",
                "user_action": "PAY_NOW",
                "return_url": body.return_url,
                "cancel_url": body.cancel_url,
            },
        }

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{base_url}/v2/checkout/orders",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation",
                },
                json=payload,
            )
        data = resp.json()
        if resp.status_code not in (200, 201):
            logger.error("PayPal order creation failed (%s): %s", resp.status_code, data)
            raise HTTPException(
                status_code=400,
                detail=str(data.get("message") or "PayPal order creation failed"),
            )

        paypal_order_id = data.get("id")
        approve_url = next(
            (link["href"] for link in data.get("links", []) if link.get("rel") == "approve"),
            None,
        )
        if paypal_order_id:
            setattr(order, "payment_intent_id", paypal_order_id)
            pp.commit(db)

        return {
            "paypal_order_id": paypal_order_id,
            "approve_url": approve_url,
            "status": data.get("status"),
            "currency": currency_code,
            "display_amount": float(converted_total),
        }
    except HTTPException as e:
        logger.exception("create_paypal_order_failed", error=str(e))
        raise
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:
        logger.error("PayPal order creation error: %s", exc)
        raise HTTPException(status_code=500, detail="PayPal payment service error")


async def capture_paypal_order(body: PayPalCaptureRequest, current_user: dict, db: Session) -> dict:
    """Capture an approved PayPal order (called after the customer approves on PayPal)."""
    configured, client_id, secret, base_url = _paypal_configured(db)
    if not configured:
        raise HTTPException(status_code=503, detail="PayPal not configured")

    order = _get_user_order(body.order_id, current_user, db)
    if order.paid_at is not None:
        raise HTTPException(status_code=409, detail="Order is already paid")

    try:
        access_token = await _paypal_get_access_token(cast(str, client_id), cast(str, secret), base_url)

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{base_url}/v2/checkout/orders/{body.paypal_order_id}/capture",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json={},
            )
        data = resp.json()
        capture_status = str(data.get("status", "") or "").upper()

        if resp.status_code in (200, 201) and capture_status == "COMPLETED":
            capture_units = data.get("purchase_units", [])
            capture_id = None
            if capture_units:
                captures = capture_units[0].get("payments", {}).get("captures", [])
                if captures:
                    capture_id = captures[0].get("id")

            _apply_successful_payment(
                order,
                f"Order #{order.id} payment via PayPal was successful.",
                db,
            )
            if capture_id:
                setattr(order, "payment_intent_id", capture_id)
            pp.commit(db)

            return {
                "status": "confirmed",
                "order_id": order.id,
                "order_status": order.status,
                "capture_id": capture_id,
                "paypal_order_id": body.paypal_order_id,
                "paid_at": order.paid_at,
            }

        if capture_status in ("VOIDED", "DECLINED"):
            if order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:
                setattr(order, "status", "failed")
                pp.add(db, 
                    Notification(
                        user_id=order.user_id,
                        type="order_update",
                        title="Payment Failed",
                        message=f"Order #{order.id} PayPal payment failed.",
                        link=f"/orders/{order.id}",
                    )
                )
                pp.commit(db)
                try:
                    event = PaymentFailedEvent.create(
                        order_id=order.id,
                        user_id=order.user_id,
                        provider="paypal",
                        message="PayPal payment failed.",
                    )
                    _event_publisher.publish(event)
                except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
                    logger.exception("PayPal: failed to publish PaymentFailedEvent for order %s", order.id)
            return {
                "status": "failed",
                "order_id": order.id,
                "order_status": order.status,
                "paypal_order_id": body.paypal_order_id,
                "paid_at": order.paid_at,
            }

        return {
            "status": "pending",
            "order_id": order.id,
            "order_status": order.status,
            "paypal_order_id": body.paypal_order_id,
            "capture_status": capture_status,
        }
    except HTTPException as e:
        logger.exception("capture_paypal_order_failed", error=str(e))
        raise
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:
        logger.error("PayPal capture error: %s", exc)
        raise HTTPException(status_code=500, detail="PayPal payment service error")


async def handle_paypal_webhook(request: Request, db: Session) -> dict:
    """Verify and process PayPal webhook event notifications."""
    import json as _json

    body_bytes = await request.body()
    try:
        event_data = _json.loads(body_bytes)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
        logger.exception("handle_paypal_webhook_failed", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid PayPal webhook payload")

    event_id = str(event_data.get("id") or "").strip()
    if event_id:
        existing = db.query(ProcessedWebhookEvent).filter(
            ProcessedWebhookEvent.event_id == event_id,
            ProcessedWebhookEvent.processor == "paypal",
        ).first()
        if existing:
            return {"status": "duplicate"}

    # Verify signature if webhook_id (stored as webhook_secret) is configured
    configured, client_id, secret, base_url = _paypal_configured(db)
    if configured:
        gw_record = _get_gateway_connection_record(db, "paypal")
        webhook_id = decrypt_secret(cast(str | None, getattr(gw_record, "webhook_secret", None))) if gw_record else None
        if client_id and secret and webhook_id:
            try:
                access_token = await _paypal_get_access_token(cast(str, client_id), cast(str, secret), base_url)
                verify_payload = {
                    "auth_algo": request.headers.get("paypal-auth-algo", ""),
                    "cert_url": request.headers.get("paypal-cert-url", ""),
                    "transmission_id": request.headers.get("paypal-transmission-id", ""),
                    "transmission_sig": request.headers.get("paypal-transmission-sig", ""),
                    "transmission_time": request.headers.get("paypal-transmission-time", ""),
                    "webhook_id": webhook_id,
                    "webhook_event": event_data,
                }
                async with httpx.AsyncClient(timeout=10) as http_client:
                    verify_resp = await http_client.post(
                        f"{base_url}/v1/notifications/verify-webhook-signature",
                        headers={
                            "Authorization": f"Bearer {access_token}",
                            "Content-Type": "application/json",
                        },
                        json=verify_payload,
                    )
                if verify_resp.json().get("verification_status") != "SUCCESS":
                    logger.warning("PayPal webhook signature failed: %s", verify_resp.text[:200])
                    raise HTTPException(status_code=400, detail="PayPal webhook signature invalid")
            except HTTPException as e:
                logger.exception("handle_paypal_webhook_failed", error=str(e))
                raise
            except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
                logger.exception("PayPal webhook verification error")

    event_type = str(event_data.get("event_type", "") or "")
    resource = event_data.get("resource", {}) if isinstance(event_data.get("resource"), dict) else {}

    if event_type == "PAYMENT.CAPTURE.COMPLETED":
        capture_id = str(resource.get("id") or "").strip()
        # PayPal puts the custom_id (our order ID) on the purchase unit or resource
        custom_id = str(resource.get("custom_id") or "").strip()
        supplementary = resource.get("supplementary_data") or {}
        pp_order_id = (supplementary.get("related_ids") or {}).get("order_id", "")
        order_ref = custom_id or pp_order_id
        if order_ref and order_ref.isdigit():
            order = db.query(Order).filter(Order.id == int(order_ref)).first()
            if order and order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:
                if capture_id:
                    setattr(order, "payment_intent_id", capture_id)
                _apply_successful_payment(
                    order,
                    f"Order #{order.id} PayPal webhook: payment captured.",
                    db,
                )
                pp.commit(db)

    elif event_type in ("PAYMENT.CAPTURE.DENIED", "PAYMENT.CAPTURE.DECLINED"):
        custom_id = str(resource.get("custom_id") or "").strip()
        if custom_id and custom_id.isdigit():
            order = db.query(Order).filter(Order.id == int(custom_id)).first()
            if order and order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:
                setattr(order, "status", "failed")
                pp.add(db, 
                    Notification(
                        user_id=order.user_id,
                        type="order_update",
                        title="Payment Failed",
                        message=f"Order #{order.id} PayPal payment failed.",
                        link=f"/orders/{order.id}",
                    )
                )
                pp.commit(db)
                try:
                    event = PaymentFailedEvent.create(
                        order_id=order.id,
                        user_id=order.user_id,
                        provider="paypal",
                        message="PayPal payment failed.",
                    )
                    _event_publisher.publish(event)
                except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
                    logger.exception("PayPal webhook: failed to publish PaymentFailedEvent for order %s", order.id)

    elif event_type == "PAYMENT.CAPTURE.REFUNDED":
        # PayPal includes the original capture ID in resource links
        capture_id = ""
        for link in resource.get("links", []):
            if isinstance(link, dict) and link.get("rel") == "up":
                capture_id = str(link.get("href", "")).rsplit("/", 2)[-2]
                break
        if not capture_id:
            capture_id = str(resource.get("custom_id") or "").strip()
        order = db.query(Order).filter(Order.payment_intent_id == capture_id).first() if capture_id else None
        if order and order.status != "refunded":
            apply_order_status_change(
                order,
                "refunded",
                db,
                refund_meta={
                    "source": "paypal_refund",
                    "transaction_ref": str(resource.get("id") or f"paypal:refund:{order.id}"),
                    "description": f"PayPal refund settled for order #{order.id}",
                    "transaction_date": datetime.now(timezone.utc).replace(tzinfo=None),
                },
            )
            pp.add(db, 
                Notification(
                    user_id=order.user_id,
                    type="order_update",
                    title="Refund Processed",
                    message=f"Your PayPal refund for Order #{order.id} has been processed.",
                    link=f"/orders/{order.id}",
                )
            )
            pp.commit(db)

    else:
        logger.debug("Unhandled PayPal webhook event: %s", event_type)

    if event_id:
        pp.add(db, ProcessedWebhookEvent(event_id=event_id, processor="paypal"))
        pp.commit(db)

    return {"status": "ok"}


async def _paypal_get_access_token(client_id: str, secret: str, base_url: str) -> str:
    """Fetch a short-lived OAuth2 client-credentials access token from PayPal."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{base_url}/v1/oauth2/token",
            headers={"Accept": "application/json", "Accept-Language": "en_US"},
            auth=(client_id, secret),
            data={"grant_type": "client_credentials"},
        )
    if resp.status_code != 200:
        logger.error("PayPal token request failed (status=%s)", resp.status_code)
        raise HTTPException(status_code=503, detail="PayPal authentication failed")
    token = resp.json().get("access_token")
    if not token:
        raise HTTPException(status_code=503, detail="PayPal authentication failed: no token returned")
    return str(token)


def _paypal_configured(db: Session) -> tuple[bool, Optional[str], Optional[str], str]:
    """Return (configured, client_id, secret, base_url) for the saved PayPal gateway connection."""
    record = _get_gateway_connection_record(db, "paypal")
    if not record:
        return False, None, None, DEFAULT_PAYPAL_SANDBOX_URL
    client_id = decrypt_secret(cast(str | None, getattr(record, "public_key", None)))
    secret = decrypt_secret(cast(str | None, getattr(record, "secret_key", None)))
    mode = str(getattr(record, "mode", "test") or "test").strip().lower()
    base_url = DEFAULT_PAYPAL_LIVE_URL if mode == "live" else DEFAULT_PAYPAL_SANDBOX_URL
    if not client_id or not secret:
        return False, None, None, base_url
    return True, client_id, secret, base_url

from providers.payments._common import *  # noqa: E402,F401,F403
from providers.payments._order import *   # noqa: E402,F401,F403
from providers.payments.config import *    # noqa: E402,F401,F403
from providers.payments.webhooks import * # noqa: E402,F401,F403
from providers.payments.stripe import *    # noqa: E402,F401,F403
from providers.payments.tap import *       # noqa: E402,F401,F403
import structlog
logger = structlog.get_logger(__name__)
from providers.payments.paytabs import *   # noqa: E402,F401,F403
from providers.payments.paypal import *    # noqa: E402,F401,F403
from providers.payments.thawani import *   # noqa: E402,F401,F403
from providers.payments.generic import *   # noqa: E402,F401,F403

