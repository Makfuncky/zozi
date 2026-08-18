"""Payment gateway provider: tap.

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


__all__ = ['create_tap_charge', '_tap_error_detail', '_finalize_tap_charge_status', 'confirm_tap_payment', 'handle_tap_webhook', '_tap_country_dial_code', '_tap_phone_payload', '_build_tap_customer', '_order_charge_total_amount']

async def refund_tap_charge(
    charge_id: str,
    amount: float,
    api_key: str,
    reason: str = "return_refund",
    api_base_url: str = "https://api.tap.company",
) -> dict:
    """Issue a Tap refund via the refund endpoint.

    Encapsulates the raw vendor HTTP call so the orders service orchestrates
    refunds without performing direct third-party requests. Returns the parsed
    JSON response from Tap.
    """
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{api_base_url}/v2/refunds",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "charge_id": charge_id,
                "amount": amount,
                "reason": reason,
            },
        )
        return resp.json()


async def create_tap_charge(body: TapChargeRequest, current_user: dict, db: Session) -> dict:
    configured, tap_key = _tap_configured(db)
    if not configured:
        raise HTTPException(status_code=503, detail="Tap Payments not configured")
    if not _payment_provider_mode_allows("tap", db):
        raise HTTPException(status_code=409, detail="Tap payments are currently disabled by admin")

    webhook_url = _resolve_tap_webhook_url(db)
    if not webhook_url:
        raise HTTPException(status_code=503, detail="Tap webhook URL not configured")
    tap_api_base_url = _resolve_tap_api_base_url(db)

    order = _get_user_order(body.order_id, current_user, db)
    if _normalized_payment_method(order) != "tap":
        raise HTTPException(status_code=409, detail="This order is not configured for Tap payment")
    if order.paid_at is not None:
        raise HTTPException(status_code=409, detail="Order is already paid")
    currency_code = _resolved_payment_currency(body.currency, body.country)
    charge_total = _order_charge_total_amount(order)
    converted_total = convert_from_aed(charge_total, currency_code)
    redirect_url = body.success_url.strip() or f"{settings.frontend_url}/checkout?tap_order_id={order.id}"
    preferred_language = str(current_user.get("preferred_language") or "en").lower()
    lang_code = "ar" if preferred_language.startswith("ar") else "en"

    payload = {
        "amount": float(converted_total),
        "currency": currency_code,
        "customer_initiated": True,
        "threeDSecure": True,
        "save_card": False,
        "description": body.description or f"ZOZI Order #{order.id}",
        "customer": _build_tap_customer(order, current_user),
        "order": {"id": str(order.id)},
        "metadata": {
            "order_id": str(order.id),
            "user_id": str(current_user["id"]),
            "payment_method": "tap",
            "shipping_country": str(getattr(order, "shipping_country", "") or ""),
            **_order_gateway_metadata(order),
        },
        "source": {"id": "src_all"},
        "redirect": {"url": redirect_url},
        "post": {"url": webhook_url},
        "reference": {
            "transaction": f"zozi_order_{order.id}",
            "order": str(order.id),
        },
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{tap_api_base_url}/v2/charges",
                headers={
                    "Authorization": f"Bearer {tap_key}",
                    "Content-Type": "application/json",
                    "accept": "application/json",
                    "lang_code": lang_code,
                },
                json=payload,
            )
        data = resp.json()
        if resp.status_code not in (200, 201):
            logger.error("Tap charge creation failed: %s", data)
            errors = data.get("errors", [{}])
            raise HTTPException(
                status_code=400,
                detail=errors[0].get("description", "Tap payment failed") if errors else "Tap payment failed",
            )

        charge_id = data.get("id")
        redirect_url = data.get("transaction", {}).get("url") or data.get("redirect", {}).get("url")
        if charge_id:
            setattr(order, "payment_intent_id", charge_id)
            pp.commit(db)
        return {
            "charge_id": charge_id,
            "redirect_url": redirect_url,
            "status": data.get("status"),
            "currency": currency_code,
            "display_amount": float(converted_total),
        }
    except HTTPException as e:
        logger.exception("create_tap_charge_failed", error=str(e))
        raise
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:
        logger.error("Tap charge error: %s", exc)
        raise HTTPException(status_code=500, detail="Tap payment service error")


def _tap_error_detail(payload: dict[str, Any], default: str) -> str:
    errors = payload.get("errors", []) if isinstance(payload, dict) else []
    if isinstance(errors, list) and errors:
        first_error = errors[0]
        if isinstance(first_error, dict):
            description = first_error.get("description")
            if description:
                return str(description)
    message = payload.get("message") if isinstance(payload, dict) else None
    return str(message or default)


def _finalize_tap_charge_status(order: Order, charge_payload: dict[str, Any], db: Session) -> dict[str, Any]:
    charge_id = str(charge_payload.get("id") or getattr(order, "payment_intent_id", "") or "").strip()
    if charge_id and not getattr(order, "payment_intent_id", None):
        setattr(order, "payment_intent_id", charge_id)

    status = str(charge_payload.get("status", "") or "").upper()

    if status == "CAPTURED":
        if order.status not in INVENTORY_RELEASE_STATUSES and order.paid_at is None:
            _apply_successful_payment(
                order,
                f"Order #{order.id} payment via Tap was successful.",
                db,
            )
            pp.commit(db)

        return {
            "status": "confirmed",
            "order_id": order.id,
            "order_status": order.status if order.status not in INVENTORY_RELEASE_STATUSES else order.status,
            "charge_id": charge_id,
            "payment_status": status,
            "paid_at": order.paid_at,
        }

    if status == "FAILED":
        if order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:
            setattr(order, "status", "failed")
            pp.add(db, 
                Notification(
                    user_id=order.user_id,
                    type="order_update",
                    title="Payment Failed",
                    message=f"Order #{order.id} Tap payment failed.",
                    link=f"/orders/{order.id}",
                )
            )
            pp.commit(db)
            try:
                event = PaymentFailedEvent.create(
                    order_id=order.id,
                    user_id=order.user_id,
                    provider="tap",
                    message="Your Tap payment could not be completed.",
                )
                _event_publisher.publish(event)
            except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
                logger.exception("Failed to publish PaymentFailedEvent for order %s", order.id)

        return {
            "status": "failed",
            "order_id": order.id,
            "order_status": order.status,
            "charge_id": charge_id,
            "payment_status": status,
            "paid_at": order.paid_at,
        }

    if status == "REFUNDED":
        if order.status != "refunded":
            apply_order_status_change(
                order,
                "refunded",
                db,
                refund_meta={
                    "source": "tap_refund",
                    "transaction_ref": f"{charge_id}:REFUNDED",
                    "description": f"Tap refund settled for order #{order.id}",
                    "transaction_date": datetime.now(timezone.utc).replace(tzinfo=None),
                },
            )
            pp.add(db, 
                Notification(
                    user_id=order.user_id,
                    type="order_update",
                    title="Refund Processed",
                    message=f"Your Tap refund for Order #{order.id} has been processed.",
                    link=f"/orders/{order.id}",
                )
            )
            pp.commit(db)

        return {
            "status": "refunded",
            "order_id": order.id,
            "order_status": order.status,
            "charge_id": charge_id,
            "payment_status": status,
            "paid_at": order.paid_at,
        }

    return {
        "status": "pending_verification",
        "order_id": order.id,
        "order_status": order.status,
        "charge_id": charge_id,
        "payment_status": status or "pending",
        "paid_at": order.paid_at,
    }


async def confirm_tap_payment(body: ConfirmTapPaymentRequest, current_user: dict, db: Session) -> dict:
    configured, tap_key = _tap_configured(db)
    if not configured:
        raise HTTPException(status_code=503, detail="Tap Payments not configured")
    tap_api_base_url = _resolve_tap_api_base_url(db)

    order = _get_user_order(body.order_id, current_user, db)
    if _normalized_payment_method(order) != "tap":
        raise HTTPException(status_code=409, detail="This order is not configured for Tap payment")

    charge_id = (body.charge_id or cast(Optional[str], getattr(order, "payment_intent_id", None)) or "").strip()
    if not charge_id:
        raise HTTPException(status_code=422, detail="charge_id is required")

    if order.paid_at is not None:
        return {
            "status": "confirmed",
            "order_id": order.id,
            "order_status": order.status,
            "charge_id": charge_id,
            "payment_status": "CAPTURED",
            "paid_at": order.paid_at,
        }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{tap_api_base_url}/v2/charges/{charge_id}",
                headers={
                    "Authorization": f"Bearer {tap_key}",
                    "accept": "application/json",
                },
            )
        data = resp.json()
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail=_tap_error_detail(data, "Tap payment verification failed"))
        return _finalize_tap_charge_status(order, data, db)
    except HTTPException as e:
        logger.exception("confirm_tap_payment_failed", error=str(e))
        raise
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:
        logger.error("Tap payment confirmation error: %s", exc)
        raise HTTPException(status_code=500, detail="Tap payment verification error")


async def handle_tap_webhook(request: Request, db: Session) -> dict:
    raw_body = await request.body()

    # ── Signature verification ────────────────────────────────────────────────
    tap_webhook_secret = _resolve_tap_webhook_secret(db)
    if tap_webhook_secret:
        sig_header = request.headers.get("hashstring", "")
        if not sig_header or not _verify_tap_signature(raw_body, sig_header, db):
            logger.warning("tap_webhook: invalid or missing signature")
            raise HTTPException(status_code=400, detail="Invalid Tap webhook signature")
    else:
        # Secret not configured — log a warning but do NOT silently accept.
        # In production, TAP_WEBHOOK_SECRET must be set.
        logger.warning(
            "tap_webhook: TAP_WEBHOOK_SECRET is not configured; "
            "signature verification is skipped. Set TAP_WEBHOOK_SECRET in production."
        )

    try:
        import json
        data = json.loads(raw_body)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
        logger.exception("handle_tap_webhook_failed", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid JSON")

    charge_id = data.get("id")
    status = data.get("status", "").upper()

    if not charge_id:
        return {"status": "ignored"}

    # ── Idempotency: skip events we have already processed ────────────────────
    # Tap does not supply a unique event ID separate from the charge ID, so we
    # use "{charge_id}:{status}" as the composite idempotency key.
    tap_event_id = f"{charge_id}:{status}"
    already_processed = db.query(ProcessedWebhookEvent).filter(
        ProcessedWebhookEvent.event_id == tap_event_id,
        ProcessedWebhookEvent.processor == "tap",
    ).first()
    if already_processed:
        logger.info("tap_webhook duplicate ignored: event_id=%s", tap_event_id)
        return {"status": "ok"}

    order = db.query(Order).filter(Order.payment_intent_id == charge_id).first()
    if not order:
        logger.warning("tap_webhook: no order for charge %s", charge_id)
        return {"status": "unknown_order"}
    _finalize_tap_charge_status(order, data, db)

    # Record event as processed (idempotency guard)
    pp.add(db, ProcessedWebhookEvent(event_id=tap_event_id, processor="tap"))
    pp.commit(db)
    logger.info("tap_webhook: charge %s order %s status=%s", charge_id, order.id, status)
    return {"status": "ok"}


def _tap_country_dial_code(country: str | None) -> str:
    code = "".join(ch for ch in str(country or "").upper() if ch.isalpha())[:2]
    return TAP_COUNTRY_DIAL_CODES.get(code, "")


def _tap_phone_payload(phone_value: str | None, country: str | None) -> dict[str, str] | None:
    digits = "".join(ch for ch in str(phone_value or "") if ch.isdigit())
    if not digits:
        return None

    if digits.startswith("00"):
        digits = digits[2:]

    dial_code = _tap_country_dial_code(country)
    if not dial_code:
        return None

    if digits.startswith(dial_code):
        digits = digits[len(dial_code):]

    digits = digits.lstrip("0")
    if not digits:
        return None

    return {
        "country_code": dial_code,
        "number": digits,
    }


def _build_tap_customer(order: Order, current_user: dict[str, Any]) -> dict[str, Any]:
    full_name = _extract_order_customer_name(order)
    if not full_name:
        username = str(current_user.get("username") or "").strip()
        if username and "@" not in username:
            full_name = username.replace(".", " ").replace("_", " ")

    if not full_name:
        email_local = str(current_user.get("email") or "").split("@", 1)[0].strip()
        if email_local:
            full_name = email_local.replace(".", " ").replace("_", " ")

    first_name, last_name = _split_customer_name(full_name)
    customer: dict[str, Any] = {
        "first_name": first_name,
        "last_name": last_name,
    }

    email = str(current_user.get("email") or "").strip()
    if email:
        customer["email"] = email

    phone_payload = _tap_phone_payload(
        cast(str | None, getattr(order, "customer_phone", None)) or cast(str | None, current_user.get("phone")),
        cast(str | None, getattr(order, "shipping_country", None)) or cast(str | None, current_user.get("preferred_country")),
    )
    if phone_payload:
        customer["phone"] = phone_payload

    if "email" not in customer and "phone" not in customer:
        raise HTTPException(status_code=422, detail="Customer email or phone is required for Tap payments")

    return customer


def _order_charge_total_amount(order: Order) -> Decimal:
    return max(
        _decimal_from_value(getattr(order, "payment_customer_total_amount", None) or getattr(order, "total_amount", 0)),
        Decimal("0"),
    )

from providers.payments._common import *  # noqa: E402,F401,F403
from providers.payments._order import *   # noqa: E402,F401,F403
from providers.payments.config import *    # noqa: E402,F401,F403
from providers.payments.webhooks import * # noqa: E402,F401,F403
from providers.payments.stripe import *    # noqa: E402,F401,F403
from providers.payments.tap import *       # noqa: E402,F401,F403
from providers.payments.paytabs import *   # noqa: E402,F401,F403
import structlog
logger = structlog.get_logger(__name__)
from providers.payments.paypal import *    # noqa: E402,F401,F403
from providers.payments.thawani import *   # noqa: E402,F401,F403
from providers.payments.generic import *   # noqa: E402,F401,F403

