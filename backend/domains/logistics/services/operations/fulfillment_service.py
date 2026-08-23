"""Fulfillment service for payment-completed events.

This service handles inventory management and order fulfillment when
payments are successfully confirmed. It is registered as a
``PaymentConfirmedEvent`` listener at lifespan startup.
"""

import logging
from typing import List

from sqlalchemy.orm import Session

from domains.orders.ports import Order, get_order_by_id

logger = logging.getLogger(__name__)


class FulfillmentService:
    """Service responsible for order fulfillment after payment confirmation."""

    def handle_payment_confirmed(self, event, db: Session) -> None:
        """Handle payment confirmation by processing order fulfillment.

        Args:
            event: Payment confirmed event (``payment_id``, ``order_id``)
            db: Database session
        """
        logger.info(
            "Processing fulfillment for payment %s (order %s)",
            event.payment_id,
            event.order_id,
        )

        order = get_order_by_id(db, event.order_id)
        if not order:
            logger.error("Order %s not found for payment %s", event.order_id, event.payment_id)
            return

        fulfillment_issues = self._process_inventory_fulfillment(order, db)

        if fulfillment_issues:
            self._handle_fulfillment_issues(order, event, fulfillment_issues, db)
            return

        self._complete_successful_fulfillment(order, event, db)

    def _process_inventory_fulfillment(self, order: Order, db: Session) -> List[str]:
        """Process inventory fulfillment for order items.

        Args:
            order: The order to fulfill
            db: Database session

        Returns:
            List of issues encountered during fulfillment
        """
        issues: List[str] = []
        for item in order.items:
            stock = getattr(item.product, "stock", None) if item.product is not None else None
            if stock is None or stock < item.quantity:
                issues.append(
                    f"Product {item.product_id} insufficient stock "
                    f"(need {item.quantity}, have {stock})"
                )
        return issues

    def _handle_fulfillment_issues(
        self, order: Order, event, issues: List[str], db: Session
    ) -> None:
        """Handle fulfillment issues after payment confirmation."""
        logger.warning(
            "Order %s fulfillment failed with issues: %s",
            order.id,
            "; ".join(issues),
        )

        order.status = "failed"
        db.add(order)
        db.flush()
        logger.info(
            "Fulfillment issues for order %s (user %s): %s",
            order.id,
            order.user_id,
            "; ".join(issues),
        )
        db.commit()

    def _complete_successful_fulfillment(self, order: Order, event, db: Session) -> None:
        """Complete successful fulfillment after payment confirmation."""
        logger.info("Successfully fulfilled order %s after payment confirmation", order.id)

        order.status = "confirmed"
        db.add(order)
        db.flush()
        logger.info(
            "Order %s confirmed after payment %s (user %s, total %s)",
            order.id,
            event.payment_id,
            order.user_id,
            order.total_amount,
        )
        db.commit()
