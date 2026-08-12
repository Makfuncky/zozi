"""Payment gateway provider: stripe.

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

from models import (
    Coupon, Order, OrderItem, Payment, PaymentGatewayConnection, PaymentProviderConfig,
    Product, Notification, ProcessedWebhookEvent, TransactionLedger, CountryConfig,
)
from events import PaymentConfirmedEvent, PaymentFailedEvent, PaymentRefundedEvent, EventPublisher, _event_publisher
from utils.config import settings
from utils.currency import (
    convert_from_aed,
    get_currency_context,
    money_to_minor_units_for_currency,
)

from providers.payments import payment_persistence as pp

logger = logging.getLogger(__name__)


__all__ = ['create_payment_intent', 'create_stripe_checkout_session', 'confirm_card_payment', 'handle_stripe_webhook', '_order_gateway_metadata', '_stripe_object_get', '_stripe_metadata_map', '_payment_intent_status', '_payment_intent_id', '_payment_intent_matches_order']

def create_payment_intent(body: PaymentIntentRequest, current_user: dict, db: Session) -> dict:
    if not _stripe_configured(db):
        raise HTTPException(status_code=503, detail="Payment service not configured")
    if not _payment_provider_mode_allows("stripe", db):
        raise HTTPException(status_code=409, detail="Stripe card payments are currently disabled by admin")
    _apply_stripe_runtime_key(db)

    order = _get_user_order(body.order_id, current_user, db)
    if _normalized_payment_method(order) != "card":
        raise HTTPException(status_code=409, detail="This order is not configured for card payment")
    if order.status in INVENTORY_RELEASE_STATUSES:
        raise HTTPException(status_code=409, detail="Order is already closed")
    if order.paid_at is not None:
        raise HTTPException(status_code=409, detail="Order is already paid")
    currency_code = _resolved_payment_currency(body.currency, body.country)
    charge_total = _order_charge_total_amount(order)
    converted_total = convert_from_aed(charge_total, currency_code)
    amount_minor = money_to_minor_units_for_currency(charge_total, currency_code)
    metadata: dict = {"user_id": str(current_user["id"])}
    metadata["order_id"] = str(order.id)
    metadata["base_currency"] = "AED"
    metadata["display_currency"] = currency_code
    metadata["zozi_amount_minor"] = str(amount_minor)
    metadata.update(_order_gateway_metadata(order))
    existing_payment_intent_id = cast(Optional[str], getattr(order, "payment_intent_id", None))

    if existing_payment_intent_id:
        try:
            existing_intent = stripe.PaymentIntent.retrieve(existing_payment_intent_id)
            existing_status = _payment_intent_status(existing_intent)
            existing_currency = str(_stripe_object_get(existing_intent, "currency", "") or "").upper()
            existing_client_secret = cast(Optional[str], _stripe_object_get(existing_intent, "client_secret", None))
            valid_existing, reason = _payment_intent_matches_order(
                existing_intent,
                order=order,
                expected_user_id=int(current_user["id"]),
                require_metadata=False,
            )
            if (
                existing_status in REUSABLE_STRIPE_INTENT_STATUSES
                and existing_currency == currency_code.upper()
                and existing_client_secret
                and valid_existing
            ):
                return {
                    "client_secret": existing_client_secret,
                    "payment_intent_id": _payment_intent_id(existing_intent) or existing_payment_intent_id,
                    "currency": currency_code,
                    "display_amount": float(converted_total),
                }
            if existing_status == "succeeded":
                _apply_successful_payment(
                    order,
                    f"Order #{order.id} payment was successful. We are preparing your order.",
                    db,
                )
                pp.commit(db)
                raise HTTPException(status_code=409, detail="Order is already paid")
            if not valid_existing:
                logger.warning(
                    "Stored payment_intent_id failed validation for order %s: %s",
                    order.id,
                    reason,
                )
        except HTTPException as e:
            logger.exception("create_payment_intent_failed", error=str(e))
            raise
        except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:
            if exc.__class__.__module__.startswith("stripe"):
                logger.warning(
                    "Could not reuse Stripe payment intent %s for order %s: %s",
                    existing_payment_intent_id,
                    order.id,
                    getattr(exc, "user_message", str(exc)),
                )
            else:
                raise

    try:
        idempotency_key = (
            f"order:{order.id}:prev:{existing_payment_intent_id or 'none'}:"
            f"currency:{currency_code.lower()}"
        )
        intent = stripe.PaymentIntent.create(
            amount=amount_minor,
            currency=currency_code.lower(),
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            metadata=metadata,
            idempotency_key=idempotency_key,
        )
        setattr(order, "payment_intent_id", intent.id)
        pp.commit(db)
        return {
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id,
            "currency": currency_code,
            "display_amount": float(converted_total),
        }
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:
        logger.exception("create_payment_intent_failed", error=str(exc))
        if exc.__class__.__module__.startswith("stripe"):
            raise HTTPException(status_code=400, detail=str(getattr(exc, "user_message", str(exc))))
        raise HTTPException(status_code=500, detail="Payment service error")


def create_stripe_checkout_session(body: StripeCheckoutSessionRequest, current_user: dict, db: Session) -> dict:
    if not _stripe_configured(db):
        raise HTTPException(status_code=503, detail="Payment service not configured")
    if not _payment_provider_mode_allows("stripe", db):
        raise HTTPException(status_code=409, detail="Stripe card payments are currently disabled by admin")
    _apply_stripe_runtime_key(db)

    order = _get_user_order(body.order_id, current_user, db)
    if _normalized_payment_method(order) != "card":
        raise HTTPException(status_code=409, detail="This order is not configured for card payment")
    if order.status in INVENTORY_RELEASE_STATUSES:
        raise HTTPException(status_code=409, detail="Order is already closed")
    if order.paid_at is not None:
        raise HTTPException(status_code=409, detail="Order is already paid")

    currency_code = _resolved_payment_currency(body.currency, body.country)
    charge_total = _order_charge_total_amount(order)
    converted_total = convert_from_aed(charge_total, currency_code)
    amount_minor = money_to_minor_units_for_currency(charge_total, currency_code)
    metadata: dict[str, str] = {
        "user_id": str(current_user["id"]),
        "order_id": str(order.id),
        "base_currency": "AED",
        "display_currency": currency_code,
        "zozi_amount_minor": str(amount_minor),
        **_order_gateway_metadata(order),
    }

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            success_url=body.success_url,
            cancel_url=body.cancel_url,
            client_reference_id=str(order.id),
            customer_email=str(current_user.get("email") or "").strip() or None,
            metadata=metadata,
            payment_method_types=["card"],
            line_items=[
                {
                    "quantity": 1,
                    "price_data": {
                        "currency": currency_code.lower(),
                        "unit_amount": amount_minor,
                        "product_data": {
                            "name": f"ZOZI Order #{order.id}",
                            "description": f"Marketplace checkout for order #{order.id}",
                        },
                    },
                }
            ],
        )
        session_id = str(_stripe_object_get(session, "id", "") or "").strip()
        if session_id:
            setattr(order, "payment_intent_id", session_id)
            pp.commit(db)
        return {
            "checkout_session_id": session_id,
            "checkout_url": _stripe_object_get(session, "url", None),
            "currency": currency_code,
            "display_amount": float(converted_total),
        }
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:
        logger.exception("create_stripe_checkout_session_failed", error=str(exc))
        if exc.__class__.__module__.startswith("stripe"):
            raise HTTPException(status_code=400, detail=str(getattr(exc, "user_message", str(exc))))
        raise HTTPException(status_code=500, detail="Payment service error")


def confirm_card_payment(body: ConfirmCardPaymentRequest, current_user: dict, db: Session) -> dict:
    """
    Confirm card payment synchronously after frontend card confirmation.

    This reduces checkout latency by finalizing the order without waiting for
    asynchronous webhook delivery while remaining idempotent with webhook flow.
    """
    order = _get_user_order(body.order_id, current_user, db)
    if _normalized_payment_method(order) != "card":
        raise HTTPException(status_code=409, detail="This order is not configured for card payment")
    if order.status in INVENTORY_RELEASE_STATUSES:
        raise HTTPException(status_code=409, detail="Order is already closed")

    if body.payment_intent_id and order.payment_intent_id and body.payment_intent_id != order.payment_intent_id:
        raise HTTPException(status_code=409, detail="payment_intent_id does not match this order")

    if order.paid_at is not None:
        return {
            "status": "confirmed",
            "order_id": order.id,
            "order_status": order.status,
            "payment_intent_id": body.payment_intent_id or cast(Optional[str], getattr(order, "payment_intent_id", None)),
            "payment_status": "succeeded",
            "paid_at": order.paid_at,
        }

    if not _stripe_configured(db):
        raise HTTPException(status_code=503, detail="Payment service not configured")
    _apply_stripe_runtime_key(db)

    payment_intent_id = body.payment_intent_id or order.payment_intent_id
    checkout_session_id = (body.checkout_session_id or "").strip()
    if checkout_session_id:
        try:
            session = stripe.checkout.Session.retrieve(checkout_session_id)
        except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:
            logger.exception("confirm_card_payment_failed", error=str(exc))
            if exc.__class__.__module__.startswith("stripe"):
                raise HTTPException(status_code=400, detail=str(getattr(exc, "user_message", str(exc))))
            raise HTTPException(status_code=502, detail="Unable to verify checkout session") from exc

        session_client_reference = str(_stripe_object_get(session, "client_reference_id", "") or "").strip()
        if session_client_reference and session_client_reference != str(order.id):
            raise HTTPException(status_code=409, detail="checkout_session_id does not belong to this order")

        session_metadata = _stripe_metadata_map(session)
        if session_metadata.get("order_id") and session_metadata.get("order_id") != str(order.id):
            raise HTTPException(status_code=409, detail="checkout_session_id does not belong to this order")

        session_payment_intent = _stripe_object_get(session, "payment_intent", None)
        if isinstance(session_payment_intent, dict):
            payment_intent_id = str(_stripe_object_get(session_payment_intent, "id", "") or "").strip() or payment_intent_id
        else:
            payment_intent_id = str(session_payment_intent or payment_intent_id or "").strip() or None

    if not payment_intent_id:
        raise HTTPException(status_code=422, detail="payment_intent_id is required")

    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:
        logger.exception("confirm_card_payment_failed", error=str(exc))
        if exc.__class__.__module__.startswith("stripe"):
            raise HTTPException(status_code=400, detail=str(getattr(exc, "user_message", str(exc))))
        raise HTTPException(status_code=502, detail="Unable to verify payment intent") from exc

    strict_metadata_match = not bool(order.payment_intent_id)
    valid_intent, validation_reason = _payment_intent_matches_order(
        intent,
        order=order,
        expected_user_id=int(current_user["id"]),
        require_metadata=strict_metadata_match,
    )
    if not valid_intent:
        logger.warning(
            "Stripe confirmation rejected for order=%s payment_intent=%s reason=%s",
            order.id,
            payment_intent_id,
            validation_reason,
        )
        raise HTTPException(status_code=409, detail="payment_intent_id does not belong to this order")

    if getattr(order, "payment_intent_id", None) != payment_intent_id:
        setattr(order, "payment_intent_id", payment_intent_id)

    intent_status = _payment_intent_status(intent)

    if intent_status == "succeeded":
        _apply_successful_payment(
            order,
            f"Order #{order.id} payment was successful. We are preparing your order.",
            db,
        )
        pp.commit(db)
        return {
            "status": "confirmed",
            "order_id": order.id,
            "order_status": order.status,
            "payment_intent_id": payment_intent_id,
            "payment_status": intent_status,
            "paid_at": order.paid_at,
        }

    if intent_status in {"requires_payment_method", "canceled"}:
        setattr(order, "status", "failed")
        pp.commit(db)
        try:
            event = PaymentFailedEvent.create(
                order_id=order.id,
                user_id=order.user_id,
                provider="stripe",
                message="Stripe payment failed or was canceled.",
            )
            _event_publisher.publish(event)
        except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
            logger.exception("Failed to publish PaymentFailedEvent for order %s", order.id)
        return {
            "status": "failed",
            "order_id": order.id,
            "order_status": order.status,
            "payment_intent_id": payment_intent_id,
            "payment_status": intent_status,
            "paid_at": order.paid_at,
        }

    return {
        "status": "pending_verification",
        "order_id": order.id,
        "order_status": order.status,
        "payment_intent_id": payment_intent_id,
        "payment_status": intent_status or "pending",
        "paid_at": order.paid_at,
    }


async def handle_stripe_webhook(request: Request, db: Session) -> dict:
    webhook_secret = _resolve_stripe_webhook_secret(db)
    if not webhook_secret:
        raise HTTPException(status_code=503, detail="Webhook secret not configured")
    _apply_stripe_runtime_key(db)

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError as e:
        logger.exception("handle_stripe_webhook_failed", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid payload")
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:
        logger.exception("handle_stripe_webhook_failed", error=str(exc))
        if exc.__class__.__name__ == "SignatureVerificationError":
            raise HTTPException(status_code=400, detail="Invalid signature")
        raise

    event_type = event["type"]
    obj = event["data"]["object"]
    stripe_event_id = event.get("id", "")

    # ── Idempotency: skip events we have already processed ────────────────────
    if stripe_event_id:
        already_processed = db.query(ProcessedWebhookEvent).filter(
            ProcessedWebhookEvent.event_id == stripe_event_id,
            ProcessedWebhookEvent.processor == "stripe",
        ).first()
        if already_processed:
            logger.info("Stripe webhook duplicate ignored: event_id=%s", stripe_event_id)
            return {"status": "ok"}

    if event_type == "payment_intent.succeeded":
        pi_id = _payment_intent_id(obj)
        metadata = _stripe_metadata_map(obj)
        metadata_order_id = metadata.get("order_id")
        order = db.query(Order).filter(Order.payment_intent_id == pi_id).first()
        if not order and metadata_order_id and metadata_order_id.isdigit():
            order = db.query(Order).filter(Order.id == int(metadata_order_id)).first()
            if order and not getattr(order, "payment_intent_id", None):
                setattr(order, "payment_intent_id", pi_id)
        if order:
            valid_intent, validation_reason = _payment_intent_matches_order(
                obj,
                order=order,
                expected_user_id=int(cast(int, order.user_id)),
                require_metadata=False,
            )
            if not valid_intent:
                logger.error(
                    "payment_intent.succeeded rejected for order %s pi=%s reason=%s",
                    order.id,
                    pi_id,
                    validation_reason,
                )
            elif order.status in INVENTORY_RELEASE_STATUSES:
                logger.warning(
                    "payment_intent.succeeded ignored for terminal order %s in status %s",
                    order.id,
                    order.status,
                )
            elif order.paid_at is not None:
                logger.info(
                    "payment_intent.succeeded duplicate ignored for already processed order %s status=%s",
                    order.id,
                    order.status,
                )
            else:
                _apply_successful_payment(
                    order,
                    f"Order #{order.id} payment was successful. We are preparing your order.",
                    db,
                )
                pp.commit(db)
                logger.info("payment_intent.succeeded: order %s status=%s", order.id, order.status)
        else:
            logger.warning("payment_intent.succeeded: no order for pi=%s", pi_id)

    elif event_type == "payment_intent.payment_failed":
        pi_id = _payment_intent_id(obj)
        metadata = _stripe_metadata_map(obj)
        metadata_order_id = metadata.get("order_id")
        last_error = _stripe_object_get(obj, "last_payment_error", {}) or {}
        error_msg = (
            last_error.get("message", "Payment failed")
            if isinstance(last_error, dict)
            else str(_stripe_object_get(last_error, "message", "Payment failed"))
        )
        order = db.query(Order).filter(Order.payment_intent_id == pi_id).first()
        if not order and metadata_order_id and metadata_order_id.isdigit():
            order = db.query(Order).filter(Order.id == int(metadata_order_id)).first()
            if order and not getattr(order, "payment_intent_id", None):
                setattr(order, "payment_intent_id", pi_id)
        if order:
            valid_intent, validation_reason = _payment_intent_matches_order(
                obj,
                order=order,
                expected_user_id=int(cast(int, order.user_id)),
                require_metadata=False,
            )
            if not valid_intent:
                logger.error(
                    "payment_intent.payment_failed rejected for order %s pi=%s reason=%s",
                    order.id,
                    pi_id,
                    validation_reason,
                )
            elif order.paid_at is not None or order.status in INVENTORY_RELEASE_STATUSES:
                logger.warning(
                    "payment_intent.payment_failed ignored for order %s in status %s paid_at=%s",
                    order.id,
                    order.status,
                    order.paid_at,
                )
            else:
                setattr(order, "status", "failed")
                pp.add(db, 
                    Notification(
                        user_id=order.user_id,
                        type="order_update",
                        title="Payment Failed",
                        message=f"Order #{order.id} payment failed: {error_msg}. Please try again.",
                        link=f"/orders/{order.id}",
                    )
                )
                pp.commit(db)
                try:
                    event = PaymentFailedEvent.create(
                        order_id=order.id,
                        user_id=order.user_id,
                        provider="stripe",
                        message=error_msg,
                    )
                    _event_publisher.publish(event)
                except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
                    logger.exception("Failed to publish PaymentFailedEvent for order %s", order.id)
                logger.info("payment_intent.payment_failed: order %s failed", order.id)

    elif event_type == "charge.refunded":
        pi_id = obj.get("payment_intent")
        if pi_id:
            order = db.query(Order).filter(Order.payment_intent_id == pi_id).first()
            if order:
                restored_inventory = apply_order_status_change(
                    order,
                    "refunded",
                    db,
                    refund_meta={
                        "source": "stripe_refund",
                        "transaction_ref": refund_ref or f"{pi_id}:refund",
                        "description": f"Stripe refund settled for order #{order.id}",
                        "transaction_date": datetime.now(timezone.utc).replace(tzinfo=None),
                    },
                )
                pp.add(db, 
                    Notification(
                        user_id=order.user_id,
                        type="order_update",
                        title="Refund Processed",
                        message=f"Your refund for Order #{order.id} has been processed.",
                        link=f"/orders/{order.id}",
                    )
                )
                pp.commit(db)
                logger.info(
                    "charge.refunded: order %s refunded restored_inventory=%s",
                    order.id,
                    restored_inventory,
                )

    else:
        logger.debug("Unhandled Stripe event: %s", event_type)

    # Record event as processed (idempotency guard)
    if stripe_event_id:
        pp.add(db, ProcessedWebhookEvent(event_id=stripe_event_id, processor="stripe"))
        pp.commit(db)

    return {"status": "ok"}


def _order_gateway_metadata(order: Order) -> dict[str, str]:
    return {
        "gateway_code": str(getattr(order, "payment_gateway_code", "") or "").strip(),
        "gateway_fee_amount": str(_decimal_from_value(getattr(order, "payment_gateway_fee_amount", 0))),
        "customer_total_amount": str(_order_charge_total_amount(order)),
    }


def _stripe_object_get(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)

    value = getattr(obj, key, None)
    if value is not None:
        return value

    getter = getattr(obj, "get", None)
    if callable(getter):
        try:
            return getter(key, default)
        except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
            logger.exception("_stripe_object_get_failed", error=str(e))
            return default
    return default


def _stripe_metadata_map(obj: Any) -> dict[str, str]:
    raw_metadata = _stripe_object_get(obj, "metadata", {}) or {}
    if isinstance(raw_metadata, dict):
        items = raw_metadata.items()
    else:
        items_fn = getattr(raw_metadata, "items", None)
        if callable(items_fn):
            try:
                items = items_fn()
            except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
                logger.exception("_stripe_metadata_map_failed", error=str(e))
                items = []
        else:
            items = []

    metadata: dict[str, str] = {}
    for key, value in items:
        if value is None:
            continue
        metadata[str(key)] = str(value)
    return metadata


def _payment_intent_status(intent: Any) -> str:
    return str(_stripe_object_get(intent, "status", "") or "").strip().lower()


def _payment_intent_id(intent: Any) -> str:
    return str(_stripe_object_get(intent, "id", "") or "").strip()


def _payment_intent_matches_order(
    intent: Any,
    *,
    order: Order,
    expected_user_id: int,
    require_metadata: bool,
) -> tuple[bool, str]:
    metadata = _stripe_metadata_map(intent)
    metadata_order_id = metadata.get("order_id")
    metadata_user_id = metadata.get("user_id")

    if require_metadata and not metadata_order_id:
        return False, "missing order_id metadata"
    if metadata_order_id and metadata_order_id != str(order.id):
        return False, f"metadata order_id mismatch ({metadata_order_id} != {order.id})"
    if metadata_user_id and metadata_user_id != str(expected_user_id):
        return False, f"metadata user_id mismatch ({metadata_user_id} != {expected_user_id})"

    metadata_amount_minor = metadata.get("zozi_amount_minor")
    intent_amount = _stripe_object_get(intent, "amount", None)
    if metadata_amount_minor and intent_amount is not None:
        try:
            if int(str(intent_amount)) != int(metadata_amount_minor):
                return (
                    False,
                    f"amount mismatch ({intent_amount} != {metadata_amount_minor})",
                )
        except (TypeError, ValueError) as e:
            logger.exception("_payment_intent_matches_order_failed", error=str(e))
            return False, "invalid payment amount metadata"

    metadata_display_currency = metadata.get("display_currency", "").strip().upper()
    intent_currency = str(_stripe_object_get(intent, "currency", "") or "").strip().upper()
    if metadata_display_currency and intent_currency and metadata_display_currency != intent_currency:
        return (
            False,
            f"currency mismatch ({intent_currency} != {metadata_display_currency})",
        )

    return True, ""


def refund_payment_intent(payment_intent: str, api_key: str | None = None):
    """Issue a Stripe refund for a payment intent.

    ``api_key`` overrides the configured secret when supplied (e.g. a
    runtime/DB-resolved key). Returns the Stripe refund object, or ``None``
    when no API key is configured.
    """
    resolved_key = api_key or settings.stripe_secret_key or os.getenv("STRIPE_SECRET_KEY", "")
    if not resolved_key:
        return None
    stripe.api_key = resolved_key
    return stripe.Refund.create(payment_intent=payment_intent)


import structlog
logger = structlog.get_logger(__name__)
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
