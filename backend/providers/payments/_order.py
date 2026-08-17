"""Order-lifecycle helpers used by payment-gateway providers.

Relocated from controllers/payments_controller.py.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from datetime import datetime, timezone
from typing import Any, Optional, cast

from sqlalchemy.orm import Session

from _legacy.models import Coupon, Order, OrderItem, Payment, Product, Notification
from events import (
    PaymentConfirmedEvent,
    PaymentFailedEvent,
    PaymentRefundedEvent,
    EventPublisher,
    _event_publisher,
)
from infrastructure.utils.config import settings
from infrastructure.utils.cache import bump_product_cache_version as _bump_product_cache_version

from providers.payments._common import *

from providers.payments import payment_persistence as pp

logger = logging.getLogger(__name__)


__all__ = ['_get_user_order', '_resolved_payment_currency', '_extract_order_customer_name', '_split_customer_name', '_order_holds_inventory', '_mark_coupon_as_used', '_increment_sales_counts', '_finalize_inventory_for_paid_order', '_restore_inventory_for_order', 'apply_order_status_change', '_confirm_order', '_apply_successful_payment', 'confirm_cash_on_delivery_order']

def _get_user_order(order_id: Optional[int], current_user: dict, db: Session) -> Order:
    if not order_id:
        raise HTTPException(status_code=422, detail="order_id is required")

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user["id"],
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


def _resolved_payment_currency(currency: str | None, country: str | None) -> str:
    context = get_currency_context(country=country, currency=currency, default_currency="AED")
    return str(context["currency_code"])


def _extract_order_customer_name(order: Order) -> str:
    shipping_address = str(getattr(order, "shipping_address", "") or "").strip()
    if not shipping_address:
        return ""

    first_segment = shipping_address.split(",", 1)[0].strip()
    if not first_segment:
        return ""

    # Shipping addresses stored by the checkout flow start with the customer's
    # full name. Guard against legacy test payloads that only store a street.
    if first_segment[0].isdigit():
        return ""

    return first_segment


def _split_customer_name(full_name: str) -> tuple[str, str]:
    normalized = " ".join(part for part in full_name.split() if part)
    if not normalized:
        return ("Customer", "ZOZI")

    parts = normalized.split(" ", 1)
    if len(parts) == 1:
        return (parts[0], "ZOZI")

    return (parts[0], parts[1])


def _order_holds_inventory(order: Order) -> bool:
    # Inventory is reserved at payment confirmation (via _finalize_inventory_for_paid_order),
    # not at order creation.  Only orders that have been confirmed/paid and not yet
    # cancelled/refunded still hold stock.
    order_status = cast(str, getattr(order, "status", ""))
    return order_status in INVENTORY_HELD_STATUSES


def _mark_coupon_as_used(order: Order, db: Session) -> None:
    coupon_code = cast(Optional[str], getattr(order, "coupon_code", None))
    if not coupon_code:
        return

    coupon = db.query(Coupon).filter(Coupon.code == coupon_code).first()
    if coupon:
        uses_count = cast(Optional[int], getattr(coupon, "uses_count", None))
        setattr(coupon, "uses_count", (uses_count or 0) + 1)


def _increment_sales_counts(order: Order, db: Session) -> None:
    """Increment Product.sales_count for each item in the order."""
    order_items = (
        db.query(OrderItem)
        .filter(OrderItem.order_id == order.id)
        .all()
    )
    if not order_items:
        return
    # Batch-load all products at once
    product_ids = list({cast(int, item.product_id) for item in order_items})
    products_map = {
        cast(int, p.id): p
        for p in db.query(Product).filter(Product.id.in_(product_ids)).all()
    }
    for item in order_items:
        product = products_map.get(cast(int, item.product_id))
        if product:
            sales_count = cast(Optional[int], getattr(product, "sales_count", None))
            quantity = cast(int, getattr(item, "quantity"))
            setattr(product, "sales_count", (sales_count or 0) + quantity)


def _finalize_inventory_for_paid_order(order: Order, db: Session) -> list[str]:
    supplier_notifs: dict[int, list[str]] = {}
    order_items = (
        db.query(OrderItem)
        .filter(OrderItem.order_id == order.id)
        .all()
    )
    requested_quantities: dict[int, int] = {}
    issues: list[str] = []

    for order_item in order_items:
        product_id = cast(int, getattr(order_item, "product_id"))
        quantity = cast(int, getattr(order_item, "quantity"))
        requested_quantities[product_id] = (
            requested_quantities.get(product_id, 0) + quantity
        )

    # Batch-load all products at once instead of one-by-one
    products_by_id: dict[int, Product] = {
        cast(int, p.id): p
        for p in db.query(Product).filter(Product.id.in_(list(requested_quantities.keys()))).all()
    } if requested_quantities else {}

    for product_id, requested_quantity in requested_quantities.items():
        product = products_by_id.get(product_id)
        if not product:
            logger.warning(
                "Payment success inventory finalization skipped missing product: order=%s product=%s",
                order.id,
                product_id,
            )
            issues.append(f"missing_product:{product_id}")
            continue

        products_by_id[product_id] = product

        stock = cast(int, getattr(product, "stock"))

        if stock < requested_quantity:
            logger.warning(
                "Inventory shortfall on payment success: order=%s product=%s available=%s requested=%s",
                order.id,
                product.id,
                stock,
                requested_quantity,
            )
            issues.append(
                f"insufficient_stock:{product.id}:available={stock}:requested={requested_quantity}"
            )

    if issues:
        return issues

    _bump_product_cache_version()
    for product_id, requested_quantity in requested_quantities.items():
        product = products_by_id[product_id]
        stock = cast(int, getattr(product, "stock"))
        new_stock = stock - requested_quantity
        setattr(product, "stock", new_stock)

        supplier_id = cast(Optional[int], getattr(product, "supplier_id", None))
        product_name = cast(str, getattr(product, "name"))
        if supplier_id is not None:
            supplier_notifs.setdefault(supplier_id, []).append(product_name)
            if new_stock <= LOW_STOCK_THRESHOLD:
                pp.add(db, 
                    Notification(
                        user_id=supplier_id,
                        type="low_stock",
                        title="Low Stock Alert",
                        message=f'"{product_name}" has only {new_stock} units left.',
                        link="/supplier/inventory",
                    )
                )

    for supplier_id, product_names in supplier_notifs.items():
        names_str = ", ".join(product_names[:3])
        if len(product_names) > 3:
            names_str += f" +{len(product_names) - 3} more"
        pp.add(db, 
            Notification(
                user_id=supplier_id,
                type="order_update",
                title="New Order Received",
                message=f"Order #{order.id} includes your product(s): {names_str}.",
                link="/supplier/orders",
            )
        )

    return []


def _restore_inventory_for_order(order: Order, db: Session) -> None:
    order_items = (
        db.query(OrderItem)
        .filter(OrderItem.order_id == order.id)
        .all()
    )

    product_ids = list({oi.product_id for oi in order_items})
    products_by_id = {
        p.id: p
        for p in db.query(Product).filter(Product.id.in_(product_ids)).all()
    } if product_ids else {}

    for order_item in order_items:
        product = products_by_id.get(order_item.product_id)
        if not product:
            logger.warning(
                "Inventory restore skipped missing product: order=%s product=%s",
                order.id,
                order_item.product_id,
            )
            continue

        stock = cast(int, getattr(product, "stock"))
        quantity = cast(int, getattr(order_item, "quantity"))
        setattr(product, "stock", stock + quantity)
    _bump_product_cache_version()


def apply_order_status_change(
    order: Order,
    target_status: str,
    db: Session,
    refund_meta: dict | None = None,
) -> bool:
    restored_inventory = False
    if (
        _order_holds_inventory(order)
        and target_status in INVENTORY_RELEASE_STATUSES
    ):
        _restore_inventory_for_order(order, db)
        restored_inventory = True

    setattr(order, "status", target_status)

    # ── Cash Management: refund ledger on cancellation/refund ──
    # The providers layer must not call ``services`` directly (CG1/CG2).
    # Publish a domain event so the subscriber creates the refund ledger,
    # refund bank transaction, and customer email out-of-band.
    if target_status in ("refunded", "cancelled"):
        try:
            reason = "cancellation" if target_status == "cancelled" else "refund"
            event = PaymentRefundedEvent.create(
                order_id=order.id,
                user_id=order.user_id,
                reason=reason,
                refund_meta=refund_meta,
            )
            _event_publisher.publish(event)
        except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
            logger.exception("Failed to publish PaymentRefundedEvent for order %s", order.id)

    return restored_inventory


def _confirm_order(
    order: Order,
    confirmation_title: str,
    confirmation_message: str,
    db: Session,
    *,
    mark_paid: bool,
) -> None:
    inventory_issues = _finalize_inventory_for_paid_order(order, db)
    if mark_paid:
        setattr(order, "paid_at", datetime.now(timezone.utc))

    if inventory_issues:
        setattr(order, "status", "failed")
        pp.add(db, 
            Notification(
                user_id=order.user_id,
                type="order_update",
                title="Order Requires Refund",
                message=(
                    f"Payment for Order #{order.id} was received, but one or more items are no longer available. "
                    "Support will contact you about a refund."
                ),
                link=f"/orders/{order.id}",
            )
        )
        logger.warning(
            "Payment success could not finalize inventory for order %s issues=%s",
            order.id,
            "; ".join(inventory_issues),
        )
        return

    setattr(order, "status", "confirmed")
    _mark_coupon_as_used(order, db)
    _increment_sales_counts(order, db)

    pp.add(db, 
        Notification(
            user_id=order.user_id,
            type="order_update",
            title=confirmation_title,
            message=confirmation_message,
            link=f"/orders/{order.id}",
        )
    )


def _publish_payment_confirmed(order: Order, db: Session, *, payment_method: str) -> None:
    """Publish a PaymentConfirmedEvent so subscribers (ledger, journal, cash,
    cache, email) run without the providers layer calling ``services`` directly.
    """
    total_amount = order.total_amount if order.total_amount is not None else (
        order.subtotal_amount if order.subtotal_amount is not None else 0
    )
    event = PaymentConfirmedEvent.create(
        payment_id="pending",
        order_id=order.id,
        amount=total_amount,
        currency=order.currency_code or "USD",
        user_id=order.user_id,
        payment_method=payment_method,
        payment_gateway=payment_method,
    )
    _event_publisher.publish(event)

    db.query(Payment).filter(
        Payment.order_id == order.id,
        Payment.provider == payment_method,
    ).update({Payment.status: "completed"})


def _apply_successful_payment(order: Order, confirmation_message: str, db: Session) -> None:
    _confirm_order(order, "Payment Confirmed", confirmation_message, db, mark_paid=True)

    # Post payment journal entry + ledger/cash/email are handled by the
    # PaymentConfirmedEvent subscriber (event-based decoupling).
    try:
        normalized = _normalized_payment_method(order)
        _publish_payment_confirmed(order, db, payment_method=normalized)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
        logger.exception("Failed to publish PaymentConfirmedEvent for order %s", order.id)


def confirm_cash_on_delivery_order(order: Order, db: Session) -> None:
    _confirm_order(
        order,
        "Order Confirmed",
        f"Order #{order.id} has been placed with Cash on Delivery. We are preparing your order.",
        db,
        mark_paid=False,
    )
    # COD also triggers the confirmation workflow (ledger/cache/email) via the
    # same domain event used by gateway payments.
    try:
        _publish_payment_confirmed(order, db, payment_method="cod")
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
        logger.exception("Failed to publish PaymentConfirmedEvent for COD order %s", order.id)

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

