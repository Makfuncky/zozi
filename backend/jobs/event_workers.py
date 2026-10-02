"""Event consumer workers for cross-domain event processing."""
from __future__ import annotations

import logging
from typing import Any

from infrastructure.events.subscriber import EventSubscriber, create_subscriber
from domains.orders.events import (
    EVENT_ORDER_CREATED, EVENT_ORDER_SHIPPED,
    EVENT_ORDER_DELIVERED, EVENT_ORDER_CANCELLED,
)
from domains.suppliers.events import (
    EVENT_SUPPLIER_VERIFIED, EVENT_SUPPLIER_REJECTED,
)
from domains.customers.events import EVENT_CUSTOMER_REGISTERED
from domains.logistics.events import (
    EVENT_SHIPMENT_CREATED, EVENT_SHIPMENT_DELIVERED,
)

ORDER_CREATED = EVENT_ORDER_CREATED
ORDER_SHIPPED = EVENT_ORDER_SHIPPED
ORDER_DELIVERED = EVENT_ORDER_DELIVERED
ORDER_CANCELLED = EVENT_ORDER_CANCELLED
PAYMENT_AUTHORIZED = "payment.authorized"
PAYMENT_FAILED = "payment.failed"
INVENTORY_RESERVED = "inventory.reserved"
CUSTOMER_REGISTERED = EVENT_CUSTOMER_REGISTERED
CUSTOMER_VERIFIED = "customer.verified"
SHIPMENT_CREATED = EVENT_SHIPMENT_CREATED
SHIPMENT_DELIVERED = EVENT_SHIPMENT_DELIVERED
SUPPLIER_APPROVED = EVENT_SUPPLIER_VERIFIED
SUPPLIER_REJECTED = EVENT_SUPPLIER_REJECTED

logger = logging.getLogger(__name__)


def _get_db():
    from infrastructure.database.database import SessionLocal
    return SessionLocal()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# ── Payment worker ────────────────────────────────────────────────────────────


def create_payments_worker() -> EventSubscriber:
    return create_subscriber(
        consumer_group="payments-worker",
        handlers={
            ORDER_CREATED: handle_order_created_for_payment,
            PAYMENT_AUTHORIZED: handle_payment_authorized,
            PAYMENT_FAILED: handle_payment_failed,
        }
    )


def handle_order_created_for_payment(event: dict) -> None:
    order_id = _safe_int(event.get("order_id"))
    if not order_id:
        return
    total_amount = event.get("total_amount", "0")
    currency = event.get("currency", "USD")
    country_code = event.get("country_code", "US")
    db = _get_db()
    try:
        from domains.payments.services.payment_service import create_payment_intent
        from decimal import Decimal
        create_payment_intent(
            order_id=order_id,
            amount=Decimal(str(total_amount)),
            currency=str(currency),
            country_code=str(country_code),
            provider="stripe",
        )
        db.commit()
        logger.info("Payment intent created for order %s", order_id)
    except Exception:
        db.rollback()
        logger.exception("Failed to create payment intent for order %s", order_id)
        raise
    finally:
        db.close()


def handle_payment_authorized(event: dict) -> None:
    order_id = _safe_int(event.get("order_id"))
    if not order_id:
        return
    db = _get_db()
    try:
        from domains.orders.services.orders_service import update_order_status
        update_order_status(order_id=order_id, status="confirmed", acting_user={"id": 0, "role": "system"}, db=db)
        db.commit()
        logger.info("Order %s confirmed after payment authorization", order_id)
    except Exception:
        db.rollback()
        logger.exception("Failed to confirm order %s after payment authorization", order_id)
        raise
    finally:
        db.close()


def handle_payment_failed(event: dict) -> None:
    order_id = _safe_int(event.get("order_id"))
    if not order_id:
        return
    error_message = event.get("error_message", "") or event.get("payload", {}).get("error_message", "")
    db = _get_db()
    try:
        from domains.orders.services.orders_service import update_order_status
        update_order_status(order_id=order_id, status="cancelled", acting_user={"id": 0, "role": "system"}, db=db)
        db.commit()
        logger.warning("Order %s cancelled due to payment failure: %s", order_id, error_message)
    except Exception:
        db.rollback()
        logger.exception("Failed to cancel order %s after payment failure", order_id)
        raise
    finally:
        db.close()


# ── Inventory worker ─────────────────────────────────────────────────────────


def create_inventory_worker() -> EventSubscriber:
    return create_subscriber(
        consumer_group="inventory-worker",
        handlers={
            ORDER_CREATED: handle_order_created_for_inventory,
            ORDER_CANCELLED: handle_order_cancelled_for_inventory,
        }
    )


def handle_order_created_for_inventory(event: dict) -> None:
    order_id = _safe_int(event.get("order_id"))
    if not order_id:
        return
    db = _get_db()
    try:
        from domains.catalog.services.products.products_service import finalize_inventory_atomic
        issues = finalize_inventory_atomic(db=db, order_id=order_id)
        db.commit()
        if issues:
            logger.warning("Order %s inventory reserved with issues: %s", order_id, issues)
        else:
            logger.info("Inventory reserved for order %s", order_id)
    except Exception:
        db.rollback()
        logger.exception("Failed to reserve inventory for order %s", order_id)
        raise
    finally:
        db.close()


def handle_order_cancelled_for_inventory(event: dict) -> None:
    order_id = _safe_int(event.get("order_id"))
    if not order_id:
        return
    db = _get_db()
    try:
        from domains.orders.models.orders import OrderItem
        from sqlalchemy import text
        from domains.catalog.models.products import Product
        order = db.query(OrderItem).filter(OrderItem.order_id == order_id, OrderItem.is_deleted == False).all()
        for item in order:
            db.execute(
                text("UPDATE catalog.products SET stock = stock + :qty, updated_at = NOW() WHERE id = :pid AND is_deleted = FALSE"),
                {"qty": item.quantity, "pid": item.product_id},
            )
        db.commit()
        logger.info("Inventory released for cancelled order %s", order_id)
    except Exception:
        db.rollback()
        logger.exception("Failed to release inventory for order %s", order_id)
        raise
    finally:
        db.close()


# ── Logistics worker ─────────────────────────────────────────────────────────


def create_logistics_worker() -> EventSubscriber:
    return create_subscriber(
        consumer_group="logistics-worker",
        handlers={
            ORDER_CREATED: handle_order_created_for_logistics,
            PAYMENT_AUTHORIZED: handle_payment_authorized_for_logistics,
            ORDER_CANCELLED: handle_order_cancelled_for_logistics,
        }
    )


def handle_order_created_for_logistics(event: dict) -> None:
    order_id = _safe_int(event.get("order_id"))
    if not order_id:
        return
    db = _get_db()
    try:
        from domains.orders.services.core.logistics import FulfillmentService
        from domains.orders.models.orders import Order
        order = db.query(Order).filter(Order.id == order_id, Order.is_deleted == False).first()
        if not order:
            logger.warning("Order %s not found for logistics fulfillment", order_id)
            return
        service = FulfillmentService(db=db)
        service._process_inventory_fulfillment(order, db)
        db.commit()
        logger.info("Logistics fulfillment initiated for order %s", order_id)
    except Exception:
        db.rollback()
        logger.exception("Failed to initiate logistics fulfillment for order %s", order_id)
        raise
    finally:
        db.close()


def handle_payment_authorized_for_logistics(event: dict) -> None:
    order_id = _safe_int(event.get("order_id"))
    if not order_id:
        return
    db = _get_db()
    try:
        from domains.orders.services.core.logistics import FulfillmentService
        from domains.orders.models.orders import Order
        order = db.query(Order).filter(Order.id == order_id, Order.is_deleted == False).first()
        if not order:
            logger.warning("Order %s not found for logistics pickup scheduling", order_id)
            return
        service = FulfillmentService(db=db)
        service._complete_successful_fulfillment(order, type("Evt", (), {"order_id": order_id})(), db)
        db.commit()
        logger.info("Carrier pickup scheduled for order %s", order_id)
    except Exception:
        db.rollback()
        logger.exception("Failed to schedule carrier pickup for order %s", order_id)
        raise
    finally:
        db.close()


def handle_order_cancelled_for_logistics(event: dict) -> None:
    order_id = _safe_int(event.get("order_id"))
    if not order_id:
        return
    db = _get_db()
    try:
        from domains.logistics.services.shipping.shipments_service import get_shipment_by_id
        from sqlalchemy import text
        result = db.execute(
            text("SELECT id FROM logistics.shipments WHERE order_id = :oid AND is_deleted = FALSE LIMIT 1"),
            {"oid": order_id},
        ).fetchone()
        if result:
            shipment_id = result[0]
            db.execute(
                text("UPDATE logistics.shipments SET is_deleted = TRUE, updated_at = NOW() WHERE id = :sid"),
                {"sid": shipment_id},
            )
            logger.info("Shipment %s cancelled for order %s", shipment_id, order_id)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to cancel shipment for order %s", order_id)
        raise
    finally:
        db.close()


# ── Notifications worker ─────────────────────────────────────────────────────


def create_notifications_worker() -> EventSubscriber:
    return create_subscriber(
        consumer_group="notifications-worker",
        handlers={
            ORDER_CREATED: handle_order_created_for_notifications,
            ORDER_SHIPPED: handle_order_shipped_for_notifications,
            ORDER_DELIVERED: handle_order_delivered_for_notifications,
            CUSTOMER_REGISTERED: handle_customer_registered_for_notifications,
            SUPPLIER_APPROVED: handle_supplier_approved_for_notifications,
            SUPPLIER_REJECTED: handle_supplier_rejected_for_notifications,
        }
    )


def handle_order_created_for_notifications(event: dict) -> None:
    order_id = _safe_int(event.get("order_id"))
    user_id = _safe_int(event.get("user_id"))
    if not order_id or not user_id:
        return
    db = _get_db()
    try:
        from domains.customers.models import User as CustomerUser
        from providers.comms.email import deliver_email
        user = db.query(CustomerUser).filter(CustomerUser.id == user_id, CustomerUser.is_deleted == False).first()
        if user and getattr(user, "email", None):
            deliver_email(
                to=user.email,
                subject=f"Order #{order_id} Confirmed",
                html=f"<p>Your order #{order_id} has been confirmed.</p>",
            )
            logger.info("Order confirmation email sent for order %s", order_id)
    except Exception:
        db.rollback()
        logger.exception("Failed to send order confirmation for order %s", order_id)
        raise
    finally:
        db.close()


def handle_order_shipped_for_notifications(event: dict) -> None:
    order_id = _safe_int(event.get("order_id"))
    tracking_number = event.get("tracking_number", "")
    if not order_id:
        return
    db = _get_db()
    try:
        from domains.customers.models import User as CustomerUser
        from domains.orders.models.orders import Order
        from providers.comms.sms import send_sms
        order = db.query(Order).filter(Order.id == order_id, Order.is_deleted == False).first()
        if order:
            user = db.query(CustomerUser).filter(CustomerUser.id == order.user_id, CustomerUser.is_deleted == False).first()
            if user and getattr(user, "phone", None):
                send_sms(
                    phone_number=user.phone,
                    message=f"Your order #{order_id} has shipped. Tracking: {tracking_number}",
                )
            logger.info("Shipment notification sent for order %s", order_id)
    except Exception:
        db.rollback()
        logger.exception("Failed to send shipment notification for order %s", order_id)
        raise
    finally:
        db.close()


def handle_order_delivered_for_notifications(event: dict) -> None:
    order_id = _safe_int(event.get("order_id"))
    if not order_id:
        return
    db = _get_db()
    try:
        from domains.customers.models import User as CustomerUser
        from domains.orders.models.orders import Order
        from providers.comms.email import deliver_email
        order = db.query(Order).filter(Order.id == order_id, Order.is_deleted == False).first()
        if order:
            user = db.query(CustomerUser).filter(CustomerUser.id == order.user_id, CustomerUser.is_deleted == False).first()
            if user and getattr(user, "email", None):
                deliver_email(
                    to=user.email,
                    subject=f"Order #{order_id} Delivered",
                    html=f"<p>Your order #{order_id} has been delivered.</p>",
                )
            logger.info("Delivery confirmation sent for order %s", order_id)
    except Exception:
        db.rollback()
        logger.exception("Failed to send delivery confirmation for order %s", order_id)
        raise
    finally:
        db.close()


def handle_customer_registered_for_notifications(event: dict) -> None:
    user_id = _safe_int(event.get("user_id"))
    email = event.get("email", "")
    if not user_id or not email:
        return
    try:
        from providers.comms.email import deliver_email
        deliver_email(
            to=email,
            subject="Welcome to ZOZI",
            html="<p>Welcome to ZOZI! We're excited to have you.</p>",
        )
        logger.info("Welcome email sent to user %s", user_id)
    except Exception:
        logger.exception("Failed to send welcome email to user %s", user_id)
        raise


def handle_supplier_approved_for_notifications(event: dict) -> None:
    supplier_id = _safe_int(event.get("supplier_id"))
    if not supplier_id:
        return
    db = _get_db()
    try:
        from domains.suppliers.models import Supplier
        from providers.comms.email import deliver_email
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id, Supplier.is_deleted == False).first()
        if supplier and getattr(supplier, "email", None):
            deliver_email(
                to=supplier.email,
                subject="Supplier Application Approved",
                html="<p>Your supplier application has been approved.</p>",
            )
            logger.info("Supplier approval notification sent for supplier %s", supplier_id)
    except Exception:
        db.rollback()
        logger.exception("Failed to send supplier approval notification for supplier %s", supplier_id)
        raise
    finally:
        db.close()


def handle_supplier_rejected_for_notifications(event: dict) -> None:
    supplier_id = _safe_int(event.get("supplier_id"))
    if not supplier_id:
        return
    db = _get_db()
    try:
        from domains.suppliers.models import Supplier
        from providers.comms.email import deliver_email
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id, Supplier.is_deleted == False).first()
        if supplier and getattr(supplier, "email", None):
            deliver_email(
                to=supplier.email,
                subject="Supplier Application Update",
                html="<p>Your supplier application requires additional review.</p>",
            )
            logger.info("Supplier rejection notification sent for supplier %s", supplier_id)
    except Exception:
        db.rollback()
        logger.exception("Failed to send supplier rejection notification for supplier %s", supplier_id)
        raise
    finally:
        db.close()


# ── Analytics worker ─────────────────────────────────────────────────────────


def create_analytics_worker() -> EventSubscriber:
    return create_subscriber(
        consumer_group="analytics-worker",
        handlers={
            ORDER_CREATED: handle_order_created_for_analytics,
            PAYMENT_AUTHORIZED: handle_payment_for_analytics,
            ORDER_SHIPPED: handle_shipment_for_analytics,
            ORDER_DELIVERED: handle_delivery_for_analytics,
            CUSTOMER_REGISTERED: handle_customer_for_analytics,
            SUPPLIER_APPROVED: handle_supplier_for_analytics,
        }
    )


def handle_order_created_for_analytics(event: dict) -> None:
    order_id = _safe_int(event.get("order_id"))
    if not order_id:
        return
    logger.info("Analytics: order.created order_id=%s user_id=%s amount=%s currency=%s country=%s",
                order_id, event.get("user_id"), event.get("total_amount"), event.get("currency"), event.get("country_code"))


def handle_payment_for_analytics(event: dict) -> None:
    order_id = _safe_int(event.get("order_id"))
    if not order_id:
        return
    logger.info("Analytics: payment.authorized order_id=%s amount=%s currency=%s gateway=%s",
                order_id, event.get("amount"), event.get("currency"), event.get("payment_gateway"))


def handle_shipment_for_analytics(event: dict) -> None:
    order_id = _safe_int(event.get("order_id"))
    if not order_id:
        return
    logger.info("Analytics: order.shipped order_id=%s shipment_id=%s carrier=%s",
                order_id, event.get("shipment_id"), event.get("carrier"))


def handle_delivery_for_analytics(event: dict) -> None:
    order_id = _safe_int(event.get("order_id"))
    if not order_id:
        return
    logger.info("Analytics: order.delivered order_id=%s delivered_at=%s",
                order_id, event.get("delivered_at"))


def handle_customer_for_analytics(event: dict) -> None:
    user_id = _safe_int(event.get("user_id"))
    if not user_id:
        return
    logger.info("Analytics: customer.registered user_id=%s email=%s country=%s",
                user_id, event.get("email"), event.get("country_code"))


def handle_supplier_for_analytics(event: dict) -> None:
    supplier_id = _safe_int(event.get("supplier_id"))
    if not supplier_id:
        return
    logger.info("Analytics: supplier.verified supplier_id=%s verified_by=%s",
                supplier_id, event.get("verified_by"))


# ── Lifecycle helpers ────────────────────────────────────────────────────────


def run_all_workers() -> list[EventSubscriber]:
    """Register and start all event workers."""
    workers = [
        create_payments_worker(),
        create_inventory_worker(),
        create_logistics_worker(),
        create_notifications_worker(),
        create_analytics_worker(),
    ]
    for worker in workers:
        worker.start()
    logger.info("Started %d event workers", len(workers))
    return workers


def stop_all_workers(workers: list[EventSubscriber]) -> None:
    """Stop all event workers."""
    for worker in workers:
        worker.stop()
    logger.info("Stopped all event workers")
