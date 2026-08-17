"""Payment gateway provider: paytabs.

Relocated from controllers/payments_controller.py.
"""
from __future__ import annotations
import structlog
logger = structlog.get_logger(__name__)

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

from _legacy.models import (
    Coupon, Order, OrderItem, Payment, PaymentGatewayConnection, PaymentProviderConfig,
    Product, Notification, ProcessedWebhookEvent, TransactionLedger, CountryConfig,
)
from events import PaymentConfirmedEvent, PaymentFailedEvent, PaymentRefundedEvent, EventPublisher, _event_publisher
from infrastructure.utils.config import settings
from infrastructure.utils.currency import (
    convert_from_aed,
    get_currency_context,
    money_to_minor_units_for_currency,
)

from providers.payments import payment_persistence as pp

logger = logging.getLogger(__name__)


__all__ = ['create_paytabs_charge', 'confirm_paytabs_payment', 'handle_paytabs_callback', '_query_paytabs_transaction', '_finalize_paytabs_transaction', '_paytabs_customer_details', '_paytabs_shipping_details', '_paytabs_transaction_reference', '_paytabs_response_status', '_paytabs_response_message']

async def create_paytabs_charge(body: PayTabsChargeRequest, current_user: dict, db: Session) -> dict:
    configured, server_key, profile_id = _paytabs_configured(db)
    if not configured:
        raise HTTPException(status_code=503, detail="PayTabs is not configured")
    if not _payment_provider_mode_allows(PAYTABS_PAYMENT_METHOD, db):
        raise HTTPException(status_code=409, detail="PayTabs payments are currently disabled by admin")

    callback_url = _resolve_paytabs_callback_url(db)
    if not callback_url:
        raise HTTPException(status_code=503, detail="PayTabs callback URL not configured")

    order = _get_user_order(body.order_id, current_user, db)
    if _normalized_payment_method(order) != PAYTABS_PAYMENT_METHOD:
        raise HTTPException(status_code=409, detail="This order is not configured for PayTabs payment")
    if order.paid_at is not None:
        raise HTTPException(status_code=409, detail="Order is already paid")

    currency_code = _resolved_payment_currency(body.currency, body.country)
    charge_total = _order_charge_total_amount(order)
    converted_total = convert_from_aed(charge_total, currency_code)
    redirect_url = body.success_url.strip() or f"{settings.frontend_url}/checkout?paytabs_order_id={order.id}"
    preferred_language = str(current_user.get("preferred_language") or "en").lower()
    payload = {
        "profile_id": int(profile_id) if str(profile_id).isdigit() else profile_id,
        "tran_type": "sale",
        "tran_class": "ecom",
        "cart_id": str(order.id),
        "cart_currency": currency_code,
        "cart_amount": float(converted_total),
        "cart_description": body.description or f"ZOZI Order #{order.id}",
        "paypage_lang": "ar" if preferred_language.startswith("ar") else "en",
        "customer_details": _paytabs_customer_details(order, current_user),
        "shipping_details": _paytabs_shipping_details(order, current_user),
        "callback": callback_url,
        "return": redirect_url,
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{_resolve_paytabs_api_base_url(db)}{DEFAULT_PAYTABS_REQUEST_PATH}",
                headers={"authorization": server_key, "content-type": "application/json"},
                json=payload,
            )
        data = response.json()
        if response.status_code not in (200, 201):
            raise HTTPException(status_code=400, detail=_paytabs_response_message(data))

        tran_ref = _paytabs_transaction_reference(data)
        if tran_ref:
            setattr(order, "payment_intent_id", tran_ref)
            pp.commit(db)

        return {
            "transaction_reference": tran_ref or None,
            "redirect_url": data.get("redirect_url"),
            "status": _paytabs_response_status(data) or "initiated",
            "currency": currency_code,
            "display_amount": float(converted_total),
        }
    except HTTPException as e:
        logger.exception("create_paytabs_charge_failed", error=str(e))
        raise
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:
        logger.error("PayTabs charge error: %s", exc)
        raise HTTPException(status_code=500, detail="PayTabs payment service error")


async def confirm_paytabs_payment(body: ConfirmPayTabsPaymentRequest, current_user: dict, db: Session) -> dict:
    order = _get_user_order(body.order_id, current_user, db)
    if _normalized_payment_method(order) != PAYTABS_PAYMENT_METHOD:
        raise HTTPException(status_code=409, detail="This order is not configured for PayTabs payment")

    if order.paid_at is not None:
        return {
            "status": "confirmed",
            "order_id": order.id,
            "order_status": order.status,
            "tran_ref": str(getattr(order, "payment_intent_id", "") or "").strip() or body.tran_ref,
            "payment_status": "approved",
            "paid_at": order.paid_at,
        }

    payload = await _query_paytabs_transaction(body.tran_ref or cast(Optional[str], getattr(order, "payment_intent_id", None)), str(order.id), db)
    return _finalize_paytabs_transaction(order, payload, db)


async def handle_paytabs_callback(request: Request, db: Session) -> dict:
    raw_body = await request.body()
    signature = request.headers.get("X-PAYTABS-SIGNATURE", "")
    webhook_secret = _resolve_paytabs_webhook_secret(db)
    
    if webhook_secret and not _verify_paytabs_signature(raw_body, signature, webhook_secret):
        logger.warning("paytabs_callback: invalid signature")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    payload: dict[str, Any] = {}

    if raw_body:
        try:
            payload = json.loads(raw_body)
        except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
            logger.exception("handle_paytabs_callback_failed", error=str(e))
            try:
                parsed = parse_qs(raw_body.decode("utf-8"), keep_blank_values=True)
                payload = {key: values[-1] for key, values in parsed.items() if values}
            except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
                logger.exception("unhandled exception", error=str(e))
                payload = {}

    for key, value in request.query_params.items():
        if key not in payload:
            payload[key] = value

    tran_ref = _paytabs_transaction_reference(payload)
    cart_id = str(payload.get("cart_id") or "").strip()
    if not tran_ref and not cart_id:
        return {"status": "ignored"}

    order = None
    if cart_id.isdigit():
        order = db.query(Order).filter(Order.id == int(cart_id)).first()
    if order is None and tran_ref:
        order = db.query(Order).filter(Order.payment_intent_id == tran_ref).first()
    if order is None:
        logger.warning("paytabs_callback: no order for tran_ref=%s cart_id=%s", tran_ref, cart_id)
        return {"status": "unknown_order"}

    queried = await _query_paytabs_transaction(tran_ref or None, cart_id or str(order.id), db)
    response_status = _paytabs_response_status(queried) or "pending"
    paytabs_event_id = f"{_paytabs_transaction_reference(queried) or tran_ref or cart_id}:{response_status}"
    already_processed = db.query(ProcessedWebhookEvent).filter(
        ProcessedWebhookEvent.event_id == paytabs_event_id,
        ProcessedWebhookEvent.processor == PAYTABS_PAYMENT_METHOD,
    ).first()
    if already_processed:
        logger.info("paytabs_callback duplicate ignored: event_id=%s", paytabs_event_id)
        return {"status": "ok"}

    _finalize_paytabs_transaction(order, queried, db)
    pp.add(db, ProcessedWebhookEvent(event_id=paytabs_event_id, processor=PAYTABS_PAYMENT_METHOD))
    pp.commit(db)
    logger.info("paytabs_callback: tran_ref=%s order=%s status=%s", _paytabs_transaction_reference(queried) or tran_ref, order.id, response_status)
    return {"status": "ok"}


async def _query_paytabs_transaction(tran_ref: str | None, cart_id: str | None, db: Session) -> dict[str, Any]:
    configured, server_key, profile_id = _paytabs_configured(db)
    if not configured:
        raise HTTPException(status_code=503, detail="PayTabs is not configured")
    payload: dict[str, Any] = {"profile_id": profile_id}
    if tran_ref:
        payload["tran_ref"] = tran_ref
    if cart_id:
        payload["cart_id"] = cart_id
    if not tran_ref and not cart_id:
        raise HTTPException(status_code=422, detail="tran_ref or cart_id is required")

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            f"{_resolve_paytabs_api_base_url(db)}{DEFAULT_PAYTABS_QUERY_PATH}",
            headers={"authorization": server_key, "content-type": "application/json"},
            json=payload,
        )
    data = response.json()
    if response.status_code not in (200, 201):
        raise HTTPException(status_code=400, detail=_paytabs_response_message(data))
    return data


def _finalize_paytabs_transaction(order: Order, payload: dict[str, Any], db: Session) -> dict[str, Any]:
    tran_ref = _paytabs_transaction_reference(payload) or str(getattr(order, "payment_intent_id", "") or "").strip()
    if tran_ref and not getattr(order, "payment_intent_id", None):
        setattr(order, "payment_intent_id", tran_ref)

    response_status = _paytabs_response_status(payload)

    if response_status in PAYTABS_SUCCESS_RESPONSE_STATUSES:
        if order.status not in INVENTORY_RELEASE_STATUSES and order.paid_at is None:
            _apply_successful_payment(order, f"Order #{order.id} payment via PayTabs was successful.", db)
            pp.commit(db)

        return {
            "status": "confirmed",
            "order_id": order.id,
            "order_status": order.status,
            "tran_ref": tran_ref,
            "payment_status": response_status,
            "paid_at": order.paid_at,
        }

    if response_status in PAYTABS_FAILURE_RESPONSE_STATUSES:
        if order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:
            setattr(order, "status", "failed")
            pp.add(db, 
                Notification(
                    user_id=order.user_id,
                    type="order_update",
                    title="Payment Failed",
                    message=f"Order #{order.id} PayTabs payment failed.",
                    link=f"/orders/{order.id}",
                )
            )
            pp.commit(db)
            try:
                event = PaymentFailedEvent.create(
                    order_id=order.id,
                    user_id=order.user_id,
                    provider="paytabs",
                    message=_paytabs_response_message(payload),
                )
                _event_publisher.publish(event)
            except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
                logger.exception("Failed to publish PaymentFailedEvent for order %s", order.id)

        return {
            "status": "failed",
            "order_id": order.id,
            "order_status": order.status,
            "tran_ref": tran_ref,
            "payment_status": response_status,
            "paid_at": order.paid_at,
        }

    return {
        "status": "pending_verification",
        "order_id": order.id,
        "order_status": order.status,
        "tran_ref": tran_ref,
        "payment_status": response_status or "pending",
        "paid_at": order.paid_at,
    }


def _paytabs_customer_details(order: Order, current_user: dict[str, Any]) -> dict[str, Any]:
    full_name = _extract_order_customer_name(order) or str(current_user.get("username") or "Customer").replace("_", " ").replace(".", " ")
    email = str(current_user.get("email") or "customer@zozi.local").strip() or "customer@zozi.local"
    phone = "".join(ch for ch in str(getattr(order, "customer_phone", None) or current_user.get("phone") or "") if ch.isdigit())
    country = str(getattr(order, "shipping_country", "") or "AE").strip().upper() or "AE"
    city = str(getattr(order, "shipping_city", "") or "Dubai").strip() or "Dubai"
    postal_code = str(getattr(order, "shipping_postal_code", "") or "00000").strip() or "00000"
    street = str(getattr(order, "shipping_address", "") or "ZOZI").strip() or "ZOZI"
    return {
        "name": full_name,
        "email": email,
        "phone": phone,
        "street1": street[:120],
        "city": city,
        "state": city,
        "country": country,
        "zip": postal_code,
    }


def _paytabs_shipping_details(order: Order, current_user: dict[str, Any]) -> dict[str, Any]:
    return _paytabs_customer_details(order, current_user)


def _paytabs_transaction_reference(payload: dict[str, Any]) -> str:
    payment_result = payload.get("payment_result") if isinstance(payload.get("payment_result"), dict) else {}
    for key in ("tran_ref", "transaction_reference"):
        value = payload.get(key) or payment_result.get(key)
        if value:
            return str(value).strip()
    return ""


def _paytabs_response_status(payload: dict[str, Any]) -> str:
    payment_result = payload.get("payment_result") if isinstance(payload.get("payment_result"), dict) else {}
    for key in ("response_status", "payment_status", "tran_status"):
        value = payment_result.get(key) or payload.get(key)
        if value:
            return str(value).strip().lower()
    return ""


def _paytabs_response_message(payload: dict[str, Any]) -> str:
    payment_result = payload.get("payment_result") if isinstance(payload.get("payment_result"), dict) else {}
    for key in ("response_message", "message"):
        value = payment_result.get(key) or payload.get(key)
        if value:
            return str(value).strip()
    return "PayTabs payment verification failed"

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
