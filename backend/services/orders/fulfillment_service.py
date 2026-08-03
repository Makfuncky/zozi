"""Fulfillment service for payment-completed events.

This service handles inventory management and order fulfillment when
payments are successfully confirmed.
"""

import logging
from typing import List

from sqlalchemy.orm import Session

from data.models import Order, Payment
from events import PaymentConfirmedEvent
from services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class FulfillmentService:
    """Service responsible for order fulfillment after payment confirmation."""

    def __init__(self, db: Session | None = None) -> None:
        """Initialize the fulfillment service."""
        self.db = db
        self.notification_service = NotificationService(db) if db else None

    def handle_payment_confirmed(self, event: PaymentConfirmedEvent, db: Session) -> None:
        """Handle payment confirmation by processing order fulfillment.

        Args:
            event: Payment confirmed event
            db: Database session
        """
        logger.info(
            "Processing fulfillment for payment %s (order %s)",
            event.payment_id,
            event.order_id,
        )

        # Get the order
        order = db.query(Order).filter(Order.id == event.order_id).first()
        if not order:
            logger.error("Order %s not found for payment %s", event.order_id, event.payment_id)
            return

        # Track fulfillment issues
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
        # This would integrate with inventory management system
        # For now, we'll simulate successful fulfillment
        issues = []

        # Check stock availability
        for item in order.items:
            if item.product.stock < item.quantity:
                issues.append(
                    f"Product {item.product_id} insufficient stock "
                    f"(need {item.quantity}, have {item.product.stock})"
                )

        return issues

    def _handle_fulfillment_issues(
        self, order: Order, event: PaymentConfirmedEvent, issues: List[str], db: Session
    ) -> None:
        """Handle fulfillment issues after payment confirmation.

        Args:
            order: The order with issues
            event: Payment confirmed event
            issues: List of fulfillment issues
            db: Database session
        """
        logger.warning(
            "Order %s fulfillment failed with issues: %s",
            order.id,
            "; ".join(issues),
        )

        # Update order status
        order.status = "failed"
        db.add(order)
        db.flush()

        # Notify user about fulfillment issues
        self.notification_service.send_fulfillment_issues_notification(
            order.user_id,
            order.id,
            event.payment_id,
            issues,
        )

        db.commit()

    def _complete_successful_fulfillment(
        self, order: Order, event: PaymentConfirmedEvent, db: Session
    ) -> None:
        """Complete successful fulfillment after payment confirmation.

        Args:
            order: The order to complete
            event: Payment confirmed event
            db: Database session
        """
        logger.info("Successfully fulfilled order %s after payment confirmation", order.id)

        # Update order status to confirmed
        order.status = "confirmed"

        # Create notification
        self.notification_service.send_fulfillment_success_notification(
            order.user_id,
            order.id,
            event.payment_id,
            order.total_amount,
        )

        db.commit()