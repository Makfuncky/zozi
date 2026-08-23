"""Payment gateway provider: generic.

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

from providers.payments import payment_persistence as pp

logger = logging.getLogger(__name__)


__all__ = ['create_generic_gateway_payment', 'handle_generic_gateway_callback', 'confirm_generic_gateway_payment', '_fill_gateway_template', '_build_generic_redirect', '_parse_generic_payload', '_resolve_generic_order', '_peek_generic_order']

def create_generic_gateway_payment(body: GenericGatewayCreateRequest, current_user: dict, db: Session) -> dict:
    """Initiate a hosted-redirect payment for any configured gateway."""
    normalized_code = _normalize_gateway_code(body.gateway_code)
    order = _get_user_order(body.order_id, current_user, db)
    if order.paid_at is not None:
        raise HTTPException(status_code=409, detail="Order is already paid")
    if order.status in INVENTORY_RELEASE_STATUSES:
        raise HTTPException(status_code=409, detail="Order is already closed")

    order_country = str(getattr(order, "shipping_country", "") or body.country or "") or None
    record = _get_gateway_connection_record(db, normalized_code, order_country)
    if record is None:
        raise HTTPException(status_code=404, detail="Gateway not found")
    if not getattr(record, "is_enabled", False) or not getattr(record, "supports_customer_checkout", False):
        raise HTTPException(status_code=409, detail="This gateway is not enabled for customer checkout")

    currency_code = _resolved_payment_currency(body.currency, body.country)
    charge_total = _order_charge_total_amount(order)
    converted_total = convert_from_aed(charge_total, currency_code)

    reference = f"gen_{order.id}_{uuid.uuid4().hex[:12]}"
    setattr(order, "payment_intent_id", reference)
    setattr(order, "payment_method", normalized_code)

    gateway = _serialize_gateway_connection(normalized_code, db, record)
    redirect = _build_generic_redirect(gateway, order, reference, currency_code, float(converted_total), db)

    pp.add(db, Payment(
        order_id=order.id,
        amount=charge_total,
        payment_method=normalized_code,
        provider=normalized_code,
        status="pending",
        intent_id=reference,
        country_code=str(getattr(order, "shipping_country", "") or body.country or "") or None,
    ))
    pp.commit(db)

    return {
        "gateway_code": normalized_code,
        "reference": reference,
        "redirect_url": redirect["redirect_url"],
        "redirect_method": redirect["redirect_method"],
        "currency": currency_code,
        "display_amount": float(converted_total),
        "status": "initiated",
    }


async def handle_generic_gateway_callback(request: Request, provider_code: str, db: Session) -> dict:
    normalized_code = _normalize_gateway_code(provider_code)
    # Resolve the gateway connection using the order's country when available so
    # per-country gateway configs are honoured even on server-to-server callbacks.
    _peek_generic_order._raw_body = await request.body()
    _peek_generic_order._query_params = request.query_params
    callback_order = _peek_generic_order(provider_code, db)
    callback_country = str(getattr(callback_order, "shipping_country", "") or "") or None
    record = _get_gateway_connection_record(db, normalized_code, callback_country)
    if record is None:
        raise HTTPException(status_code=404, detail="Gateway not found")

    extra = _json_load_dict(getattr(record, "extra_config_json", None)) if record else {}
    webhook_secret = _optional_text(getattr(record, "webhook_secret", None))
    raw_body = await request.body()
    _payload_hash = hashlib.sha256(raw_body or b"").hexdigest()
    if webhook_secret:
        signature = request.headers.get("X-SIGNATURE") or request.headers.get("X-GATEWAY-SIGNATURE") or ""
        if not _verify_paytabs_signature(raw_body, signature, webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = _parse_generic_payload(raw_body, request.query_params)
    status_field = str(extra.get("status_field", "status") or "status")
    success_values = [str(v).lower() for v in (extra.get("success_values") or list(_GENERIC_DEFAULT_SUCCESS_VALUES))]
    tran_ref_field = str(extra.get("transaction_ref_field", "tran_ref") or "tran_ref")
    order_id_field = str(extra.get("order_id_field", "cart_id") or "cart_id")

    order = _resolve_generic_order(payload, normalized_code, db)
    if order is None:
        logger.warning("generic_callback %s: no order resolved", normalized_code)
        return {"status": "unknown_order"}

    resolved_status = str(payload.get(status_field) or payload.get("response_status") or "").lower()
    tran_ref = payload.get(tran_ref_field) or str(getattr(order, "payment_intent_id", "") or "").strip()
    event_id = f"{normalized_code}:{tran_ref or order.id}:{resolved_status}"
    already = db.query(ProcessedWebhookEvent).filter(
        ProcessedWebhookEvent.event_id == event_id,
        ProcessedWebhookEvent.processor == normalized_code,
    ).first()
    if already:
        return {"status": "ok"}

    success = resolved_status in success_values
    if not resolved_status:
        # No explicit status delivered (e.g. redirect-style return). Treat the
        # callback itself as an authorization to mark the order paid when the
        # gateway is configured without a status field.
        success = True

    if success and order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:
        if tran_ref:
            setattr(order, "payment_intent_id", tran_ref)
        _apply_successful_payment(order, f"Order #{order.id} payment via {normalized_code} was successful.", db)
        pp.add(db, ProcessedWebhookEvent(event_id=event_id, processor=normalized_code, payload_hash=_payload_hash))
        pp.commit(db)
        return {"status": "ok", "order_id": order.id, "result": "confirmed"}

    if not success and order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:
        setattr(order, "status", "failed")
        pp.add(db, ProcessedWebhookEvent(event_id=event_id, processor=normalized_code, payload_hash=_payload_hash))
        pp.commit(db)
        return {"status": "ok", "order_id": order.id, "result": "failed"}

    pp.add(db, ProcessedWebhookEvent(event_id=event_id, processor=normalized_code))
    pp.commit(db)
    return {"status": "ok", "order_id": order.id}


def confirm_generic_gateway_payment(body: ConfirmGenericGatewayRequest, current_user: dict, db: Session) -> dict:
    order = _get_user_order(body.order_id, current_user, db)
    if order.paid_at is not None:
        return {"status": "confirmed", "order_id": order.id, "order_status": order.status, "payment_status": "approved", "paid_at": order.paid_at}

    normalized_code = _normalize_gateway_code(body.gateway_code)
    order_country = str(getattr(order, "shipping_country", "") or body.country or "") or None
    record = _get_gateway_connection_record(db, normalized_code, order_country)
    if record is None:
        return {"status": "pending", "order_id": order.id, "order_status": order.status, "payment_status": "pending", "paid_at": order.paid_at}

    extra = _json_load_dict(getattr(record, "extra_config_json", None)) or {}
    reference = body.reference or str(getattr(order, "payment_intent_id", "") or "")

    # Optionally poll the provider for the authoritative payment status before
    # trusting the redirect return. This makes the plug-and-play confirm work
    # even for gateways that do not post a server-side callback.
    verify_result = _generic_verify_payment(extra, record, order, reference, db)
    if verify_result == "success":
        _apply_successful_payment(order, f"Order #{order.id} payment via {normalized_code} was successful.", db)
        pp.commit(db)
        return {"status": "confirmed", "order_id": order.id, "order_status": order.status, "payment_status": "approved", "paid_at": order.paid_at}
    if verify_result == "failed":
        setattr(order, "status", "failed")
        pp.commit(db)
        return {"status": "failed", "order_id": order.id, "order_status": order.status, "payment_status": "declined", "paid_at": order.paid_at}

    # If a prior callback already recorded the payment as completed, finalize.
    payment = db.query(Payment).filter(
        Payment.order_id == order.id,
        Payment.provider == normalized_code,
    ).order_by(Payment.id.desc()).first()
    if payment and payment.status == "completed":
        _apply_successful_payment(order, f"Order #{order.id} payment via {normalized_code} was successful.", db)
        pp.commit(db)
        return {"status": "confirmed", "order_id": order.id, "order_status": order.status, "payment_status": "approved", "paid_at": order.paid_at}

    return {"status": "pending", "order_id": order.id, "order_status": order.status, "payment_status": "pending", "paid_at": order.paid_at}


def _fill_gateway_template(template: str, ctx: dict[str, Any]) -> str:
    def repl(match: "re.Match[str]") -> str:
        key = match.group(1)
        value = ctx.get(key, "")
        return str(value if value is not None else "")

    return re.sub(r"\{([a-zA-Z0-9_]+)\}", repl, template)


def _build_generic_redirect(
    gateway: PaymentGatewayConnectionResponse,
    order: Order,
    reference: str,
    currency_code: str,
    converted_total: float,
    db: Session,
) -> dict[str, Any]:
    record = _get_gateway_connection_record(db, gateway.provider_code)
    extra = _json_load_dict(getattr(record, "extra_config_json", None)) if record else {}

    callback_url = f"{_resolve_gateway_callback_base(db, gateway.provider_code)}/payments/generic/{gateway.provider_code}/callback"
    ctx: dict[str, Any] = {
        "order_id": order.id,
        "amount": converted_total,
        "currency": currency_code,
        "reference": reference,
        "callback_url": callback_url,
        "success_url": "",
        "cancel_url": "",
        "customer_email": "",
        "customer_name": "",
        "description": f"ZOZI Order #{order.id}",
    }

    create_url = _optional_text(extra.get("create_url"))
    if create_url:
        create_method = str(extra.get("create_method", "POST")).upper()
        auth_header_tpl = _optional_text(extra.get("create_auth_header"))
        headers: dict[str, str] = {"content-type": "application/json", "accept": "application/json"}
        if auth_header_tpl:
            headers["Authorization"] = _fill_gateway_template(auth_header_tpl, {**ctx, "secret_key": _optional_text(getattr(record, "secret_key", None)) or ""})
        body_fields = extra.get("create_body") or {}
        body: dict[str, Any] = {}
        for logical, actual in body_fields.items():
            body[actual] = ctx.get(logical)
        body["order_id"] = order.id
        body["amount"] = converted_total
        body["currency"] = currency_code
        body["customer_email"] = getattr(order, "customer_email", None) or ctx["customer_email"]
        body["customer_name"] = getattr(order, "customer_name", None) or ctx["customer_name"]
        body["reference"] = reference
        body["callback_url"] = callback_url
        body["return_url"] = ctx["success_url"] or f"{settings.frontend_url}/checkout?generic_order_id={order.id}&gateway={gateway.provider_code}"
        try:
            with httpx.Client(timeout=20) as client:
                resp = client.request(create_method, create_url, headers=headers, json=body)
                if resp.status_code >= 400:
                    raise HTTPException(status_code=502, detail=f"Gateway '{gateway.provider_code}' create call failed ({resp.status_code})")
                data = resp.json()
        except HTTPException as e:
            logger.exception("_build_generic_redirect_failed", error=str(e))
            raise
        except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:
            logger.error("generic gateway create call error: %s", exc)
            raise HTTPException(status_code=502, detail="Gateway connection error")
        redirect_url = _optional_text(data.get(str(extra.get("redirect_url_field", "redirect_url"))))
        redirect_method = str(extra.get("redirect_method", "GET")).upper()
        if not redirect_url:
            raise HTTPException(status_code=502, detail="Gateway did not return a redirect URL")
        return {"redirect_url": redirect_url, "redirect_method": redirect_method, "reference": reference}

    template = _optional_text(extra.get("redirect_url_template")) or _optional_text(gateway.api_base_url)
    if not template:
        raise HTTPException(status_code=503, detail="Gateway redirect URL is not configured")
    return {"redirect_url": _fill_gateway_template(template, ctx), "redirect_method": "GET", "reference": reference}


def _parse_generic_payload(raw_body: bytes, query_params) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if raw_body:
        try:
            payload = json.loads(raw_body)
        except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
            logger.exception("_parse_generic_payload_failed", error=str(e))
            try:
                parsed = parse_qs(raw_body.decode("utf-8"), keep_blank_values=True)
                payload = {k: v[-1] for k, v in parsed.items() if v}
            except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
                logger.exception("unhandled exception", error=str(e))
                payload = {}
    for key, value in query_params.items():
        if key not in payload:
            payload[key] = value
    return payload


def _resolve_generic_order(payload: dict[str, Any], provider_code: str, db: Session) -> Optional[Order]:
    order_id_field = str(payload.get("order_id_field", "cart_id") or "cart_id")
    order_id_value = payload.get(order_id_field) or payload.get("order_id") or payload.get("cart_id")
    tran_ref = (
        payload.get("tran_ref")
        or payload.get("reference")
        or payload.get("transaction_ref")
        or payload.get("payment_ref")
    )

    if order_id_value and str(order_id_value).isdigit():
        order = db.query(Order).filter(Order.id == int(order_id_value)).first()
        if order:
            return order
    if tran_ref:
        order = db.query(Order).filter(Order.payment_intent_id == str(tran_ref).strip()).first()
        if order:
            return order
    return None


def _peek_generic_order(provider_code: str, db: Session) -> Optional["Order"]:
    """Best-effort order lookup from the current request body for country resolution.

    Used by the callback handler to pick the correct per-country gateway config
    without duplicating the full payload parsing/resolution done later.
    """
    try:
        raw_body = getattr(_peek_generic_order, "_raw_body", None)
        query_params = getattr(_peek_generic_order, "_query_params", None)
        if raw_body is None:
            return None
        payload = _parse_generic_payload(raw_body, query_params or {})
        return _resolve_generic_order(payload, provider_code, db)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
        logger.exception("_peek_generic_order_failed", error=str(e))
        return None

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
