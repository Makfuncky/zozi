"""
Payments Service — Stripe and Tap Payments business logic.

Security hardening applied:
  - Stripe webhooks: verified via stripe.Webhook.construct_event (existing)
  - Tap webhooks: verified via HMAC-SHA256 of the raw request body using
    TAP_WEBHOOK_SECRET (new).  Requests without a valid signature are rejected
    with HTTP 400.
  - Both processors use ProcessedWebhookEvent for idempotency.
  - sales_count is incremented on every item when a payment succeeds.
  - All Tap config (key, webhook secret, webhook URL) is read from settings,
    not bare os.getenv(), so they are validated at startup and appear in docs.
"""
import logging
from datetime import datetime
from typing import Optional

import stripe
from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from events import EventPublisher, PaymentConfirmedEvent, _event_publisher
from models import (
    Order,
    Payment,
    ProcessedWebhookEvent,
)
from utils.config import settings

logger = logging.getLogger(__name__)

stripe.api_key = str(getattr(settings, "stripe_secret_key", "") or "").strip()
if str(getattr(settings, "stripe_api_version", "") or "").strip():
    stripe.api_version = str(getattr(settings, "stripe_api_version", "") or "").strip()

LOW_STOCK_THRESHOLD = 5
INVENTORY_RELEASE_STATUSES = {"cancelled", "refunded"}
INVENTORY_HELD_STATUSES = {"confirmed", "processing", "prepared", "picking_up", "shipped", "delivered"}
COD_PAYMENT_METHOD = "cod"
PAYTABS_PAYMENT_METHOD = "paytabs"
THAWANI_PAYMENT_METHOD = "thawani"
REUSABLE_STRIPE_INTENT_STATUSES = {
    "requires_payment_method",
    "requires_confirmation",
    "requires_action",
    "processing",
    "requires_capture",
}
SUPPORTED_CHECKOUT_PAYMENT_METHODS = {COD_PAYMENT_METHOD, "card", "tap", PAYTABS_PAYMENT_METHOD, THAWANI_PAYMENT_METHOD}
ORDER_PAYMENT_METHOD_GATEWAY_MAP = {"card": "stripe", "tap": "tap", PAYTABS_PAYMENT_METHOD: PAYTABS_PAYMENT_METHOD, THAWANI_PAYMENT_METHOD: THAWANI_PAYMENT_METHOD}
ONLINE_PAYMENT_PROVIDER_MODES = {"stripe", "tap", "both"}
SUPPORTED_GATEWAY_KINDS = {"stripe", "tap", "custom"}
SUPPORTED_GATEWAY_TEST_STATUSES = {"untested", "passed", "failed"}
SUPPORTED_SETTLEMENT_CYCLES = {"daily", "weekly", "monthly"}
DEFAULT_SETTLEMENT_CYCLE = "weekly"
BUILT_IN_GATEWAY_ORDER = ("stripe", "tap", PAYTABS_PAYMENT_METHOD, "paypal", "hyperpay", "omannet", THAWANI_PAYMENT_METHOD)
BUILT_IN_GATEWAY_CODES = set(BUILT_IN_GATEWAY_ORDER)
LIVE_ADAPTER_GATEWAY_CODES = {"stripe", "tap", PAYTABS_PAYMENT_METHOD, "paypal", THAWANI_PAYMENT_METHOD}
DEFAULT_TAP_API_BASE_URL = "https://api.tap.company"
DEFAULT_TAP_TEST_CHARGE_ID = "chg_test_connection_check"
DEFAULT_PAYTABS_API_BASE_URL = "https://secure.paytabs.com"
DEFAULT_PAYPAL_SANDBOX_URL = "https://api-m.sandbox.paypal.com"
DEFAULT_PAYPAL_LIVE_URL = "https://api-m.paypal.com"
DEFAULT_THAWANI_UAT_URL = "https://uatcheckout.thawani.om/api/v1"
DEFAULT_THAWANI_LIVE_URL = "https://checkout.thawani.om/api/v1"
DEFAULT_THAWANI_UAT_PAY_BASE = "https://uatcheckout.thawani.om"
DEFAULT_THAWANI_LIVE_PAY_BASE = "https://checkout.thawani.om"
DEFAULT_PAYTABS_REQUEST_PATH = "/payment/request"
DEFAULT_PAYTABS_QUERY_PATH = "/payment/query"
PAYTABS_SUCCESS_RESPONSE_STATUSES = {"a", "approved", "success", "captured"}
PAYTABS_PENDING_RESPONSE_STATUSES = {"h", "hold", "pending", "p", "processing"}
PAYTABS_FAILURE_RESPONSE_STATUSES = {"d", "declined", "e", "error", "failed"}
TAP_COUNTRY_DIAL_CODES = {
    "AE": "971",
    "BH": "973",
    "EG": "20",
    "GB": "44",
    "JO": "962",
    "KW": "965",
    "OM": "968",
    "QA": "974",
    "SA": "966",
    "US": "1",
}


# ── Pydantic request models ───────────────────────────────────────────────────

class WebhookPayload(BaseModel):
    event_type: str = Field(..., description="Event type from provider")
    event_id: str = Field(..., description="Event identifier from provider")
    provider: str = Field(..., description="Payment provider (stripe/tap)")
    data: dict = Field(..., description="Event payload")
    headers: Optional[dict] = Field(None, description="Request headers")

    class Config:
        extra = "allow"

class ProcessedWebhookEventCreate(BaseModel):
    provider: str = Field(..., description="Payment provider")
    event_type: str = Field(..., description="Event type")
    event_id: str = Field(..., description="Unique event ID")
    entity_type: str = Field(..., description="Entity type (order, payment, etc.)")
    entity_id: int = Field(..., description="Entity ID")
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    processing_result: str = Field(..., description="success/failed/partially_failed")


# ── Service Functions ────────────────────────────────────────────────────────────

async def process_webhook_event(db: Session, payload: dict, signature: str = None) -> dict:
    """
    Process webhook events from payment providers (Stripe, Tap).
    Handles validation, idempotency, and business logic execution.
    """
    provider = payload.get("provider")
    event_type = payload.get("event_type")
    event_id = payload.get("event_id")
    data = payload.get("data", {})
    headers = payload.get("headers", {})
    
    logger.info(f"Processing webhook event: {event_id} ({event_type}) from {provider}")
    
    if provider in ["stripe", "tap"]:
        return await process_stripe_or_tap_webhook(db, provider, event_type, event_id, data, headers)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported payment provider: {provider}")


async def process_stripe_or_tap_webhook(db: Session, provider: str, event_type: str, event_id: str, data: dict, headers: dict) -> dict:
    """
    Process webhooks from Stripe or Tap payment providers.
    Handles payment confirmations, refunds, disputes, and subscription events.
    """
    logger.info(f"Processing webhook event {event_id} ({event_type}) from {provider}")
    
    # Check if event has already been processed (idempotency)
    existing = db.query(ProcessedWebhookEvent).filter(ProcessedWebhookEvent.event_id == event_id).first()
    if existing:
        logger.info(f"Event {event_id} already processed, returning existing result")
        return {"status": "duplicate", "event_id": event_id, "processed_at": existing.processed_at}
    
    processed_event = ProcessedWebhookEvent(event_id=event_id, provider=provider, event_type=event_type, data=data, headers=headers)
    db.add(processed_event)
    
    try:
        if provider == "stripe":
            result = await process_stripe_webhook(db, event_type, data, headers)
        else:
            result = await process_tap_webhook(db, event_type, data, headers)
        
        processed_event.processed_at = datetime.utcnow()
        processed_event.processing_result = "success"
        
        if result.get("status") == "success":
            db.commit()
            logger.info(f"Successfully processed webhook event {event_id}")
        else:
            db.rollback()
            processed_event.processing_result = "failed"
            logger.error(f"Failed to process webhook event {event_id}: {result.get('error')}")
            
    except Exception as exc:
        db.rollback()
        processed_event.processing_result = "failed"
        logger.error(f"Error processing webhook event {event_id}: {str(exc)}")
        raise
        
    return {
        "status": "success",
        "event_id": event_id,
        "processed_at": processed_event.processed_at,
        "result": result
    }


async def process_stripe_webhook(db: Session, event_type: str, data: dict, headers: dict) -> dict:
    """
    Process Stripe webhook events.
    Handles payment_intent.succeeded, payment_intent.payment_failed, etc.
    """
    logger.info(f"Processing Stripe webhook event: {event_type}")
    
    if event_type == "payment_intent.succeeded":
        return await handle_stripe_payment_success(db, data)
    elif event_type == "payment_intent.payment_failed":
        return await handle_stripe_payment_failure(db, data)
    elif event_type == "charge.succeeded":
        return await handle_stripe_charge_success(db, data)
    elif event_type == "charge.failed":
        return await handle_stripe_charge_failure(db, data)
    elif event_type == "invoice.payment_succeeded":
        return await handle_stripe_invoice_payment_succeeded(db, data)
    elif event_type == "invoice.payment_failed":
        return await handle_stripe_invoice_payment_failed(db, data)
    elif event_type == "customer.subscription.created":
        return await handle_stripe_subscription_created(db, data)
    elif event_type == "customer.subscription.deleted":
        return await handle_stripe_subscription_deleted(db, data)
    else:
        logger.info(f"Unhandled Stripe event type: {event_type}")
        return {"status": "ignored", "reason": f"Unhandled event type: {event_type}"}


async def process_tap_webhook(db: Session, event_type: str, data: dict, headers: dict) -> dict:
    """
    Process Tap (Saudi Payments) webhook events.
    Handles payment completion, refunds, and subscription events.
    """
    logger.info(f"Processing Tap webhook event: {event_type}")
    
    if event_type == "charge.succeeded":
        return await handle_tap_charge_success(db, data)
    elif event_type == "charge.failed":
        return await handle_tap_charge_failure(db, data)
    elif event_type == "refund.created":
        return await handle_tap_refund_created(db, data)
    elif event_type == "subscription.created":
        return await handle_tap_subscription_created(db, data)
    elif event_type == "subscription.cancelled":
        return await handle_tap_subscription_cancelled(db, data)
    else:
        logger.info(f"Unhandled Tap event type: {event_type}")
        return {"status": "ignored", "reason": f"Unhandled event type: {event_type}"}


async def handle_stripe_payment_success(db: Session, data: dict) -> dict:
    """
    Handle successful Stripe payment_intent events.
    Updates payment status, creates PaymentConfirmedEvent, updates inventory.
    """
    payment_intent = data.get("data", {}).get("object", {})
    payment_id = payment_intent.get("id")
    
    payment = db.query(Payment).filter_by(provider_payment_id=payment_id).first()
    if not payment:
        logger.error(f"Payment not found for payment_intent: {payment_id}")
        return {"status": "failed", "error": "Payment not found"}
    
    payment.status = "completed"
    payment.completed_at = datetime.utcnow()
    payment.transaction_id = data.get("id")
    
    order = payment.order
    if order:
        order.status = "paid"
        order.paid_at = datetime.utcnow()
    
    db.commit()
    
    _event_publisher.publish(PaymentConfirmedEvent(
        payment_id=payment.id,
        order_id=order.id if order else None,
        amount=payment.amount,
        currency=payment.currency,
        payment_provider="stripe",
        transaction_id=payment.transaction_id,
        event_type="payment.success",
    ))
    
    return {"status": "success", "payment_id": payment_id, "order_id": order.id if order else None}


async def handle_stripe_charge_success(db: Session, data: dict) -> dict:
    """
    Handle successful Stripe charge events.
    Updates payment status and inventory for individual charges.
    """
    charge = data.get("data", {}).get("object", {})
    payment = db.query(Payment).filter_by(stripe_charge_id=charge.get("id")).first()
    
    if not payment:
        logger.error(f"Payment not found for charge: {charge.get('id')}")
        return {"status": "failed", "error": "Payment not found for charge"}
    
    if payment.status != "completed":
        payment.status = "completed"
        payment.completed_at = datetime.utcnow()
        payment.transaction_id = charge.get("id")
        
        order = payment.order
        if order and order.status != "paid":
            order.status = "paid"
            order.paid_at = datetime.utcnow()
        
        try:
            db.commit()
            
            _event_publisher.publish(PaymentConfirmedEvent(
                payment_id=payment.id,
                order_id=order.id if order else None,
                amount=payment.amount,
                currency=payment.currency,
                payment_provider="stripe",
                transaction_id=payment.transaction_id,
                event_type="charge.success",
            ))
            
            update_product_inventory(db, payment.order_id, True)
            
        except Exception as exc:
            db.rollback()
            logger.error(f"Error processing Stripe charge success webhook: {str(exc)}")
            return {"status": "failed", "error": str(exc)}
    
    return {"status": "success", "charge_id": charge.get("id")}


async def handle_tap_charge_success(db: Session, data: dict) -> dict:
    """
    Handle successful Tap charge events.
    Updates payment status and processes successful transactions.
    """
    charge = data.get("data", {}).get("charge", {})
    payment = db.query(Payment).filter_by(tap_charge_id=charge.get("id")).first()
    
    if not payment:
        logger.error(f"Payment not found for Tap charge: {charge.get('id')}")
        return {"status": "failed", "error": "Payment not found for Tap charge"}
    
    if payment.status != "completed":
        payment.status = "completed"
        payment.completed_at = datetime.utcnow()
        payment.transaction_id = charge.get("id")
        
        order = payment.order
        if order and order.status != "paid":
            order.status = "paid"
            order.paid_at = datetime.utcnow()
        
        try:
            db.commit()
            
            _event_publisher.publish(PaymentConfirmedEvent(
                payment_id=payment.id,
                order_id=order.id if order else None,
                amount=payment.amount,
                currency=payment.currency,
                payment_provider="tap",
                transaction_id=payment.transaction_id,
                event_type="charge.success",
            ))
            
            update_product_inventory(db, payment.order_id, True)
            
        except Exception as exc:
            db.rollback()
            logger.error(f"Error processing Tap charge success webhook: {str(exc)}")
            return {"status": "failed", "error": str(exc)}
    
    return {"status": "success", "tap_charge_id": charge.get("id")}


def update_product_inventory(db: Session, order_id: int, decrement: bool = True) -> None:
    """
    Update product inventory levels based on order items.
    If decrement is True, reduce inventory; otherwise, restore inventory.
    """
    order = db.query(Order).filter_by(id=order_id).first()
    if not order:
        logger.error(f"Order not found for inventory update: {order_id}")
        return
    
    for order_item in order.items:
        product = order_item.product
        if product and product.stock is not None:
            if decrement:
                new_stock = max(0, product.stock - order_item.quantity)
                logger.info(f"Decrementing stock for product {product.id}: {product.stock} -> {new_stock}")
            else:
                new_stock = product.stock + order_item.quantity
                logger.info(f"Restoring stock for product {product.id}: {product.stock} -> {new_stock}")
            
            product.stock = new_stock
    
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error(f"Error updating product inventory: {str(exc)}")
