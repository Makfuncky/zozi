"""Payment-related domain events.

This module defines events that occur when payments are completed,
allowing for asynchronous processing of payment-related workflows.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

@dataclass
class PaymentConfirmedEvent:
    """Event triggered when a payment is successfully confirmed.

    Attributes:
        payment_id: The ID of the completed payment
        order_id: The ID of the associated order
        amount: The payment amount
        currency: The payment currency
        user_id: The ID of the user who made the payment
        payment_method: The method used for payment (e.g., 'card', 'cod')
        payment_gateway: The payment provider (e.g., 'stripe', 'tap')
        event_id: Unique identifier for this event
    """

    payment_id: str
    order_id: int
    amount: Decimal
    currency: str
    user_id: int
    payment_method: str
    payment_gateway: str
    event_id: str

    @classmethod
    def create(
        cls,
        payment_id: str,
        order_id: int,
        amount: Decimal,
        currency: str,
        user_id: int,
        payment_method: str,
        payment_gateway: str,
    ) -> "PaymentConfirmedEvent":
        """Create a new payment confirmed event."""
        import uuid

        return cls(
            payment_id=payment_id,
            order_id=order_id,
            amount=amount,
            currency=currency,
            user_id=user_id,
            payment_method=payment_method,
            payment_gateway=payment_gateway,
            event_id=str(uuid.uuid4()),
        )

    def to_dict(self) -> dict:
        """Convert event to dictionary for serialization."""
        return {
            "event_type": "PaymentConfirmed",
            "event_id": self.event_id,
            "payment_id": self.payment_id,
            "order_id": self.order_id,
            "amount": str(self.amount),
            "currency": self.currency,
            "user_id": self.user_id,
            "payment_method": self.payment_method,
            "payment_gateway": self.payment_gateway,
            "timestamp": getattr(self, "_timestamp", None),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PaymentConfirmedEvent":
        """Create event from dictionary."""
        return cls(
            payment_id=data["payment_id"],
            order_id=data["order_id"],
            amount=Decimal(data["amount"]),
            currency=data["currency"],
            user_id=data["user_id"],
            payment_method=data["payment_method"],
            payment_gateway=data["payment_gateway"],
            event_id=data["event_id"],
        )


@dataclass
class PaymentFailedEvent:
    """Event triggered when a payment fails or is cancelled.

    Attributes mirror :class:`PaymentConfirmedEvent` so listeners can treat the
    two as interchangeable domain events.
    """

    payment_id: str
    order_id: int
    amount: Decimal
    currency: str
    user_id: int
    payment_method: str
    payment_gateway: str
    error_message: str = ""
    event_id: str = ""

    @classmethod
    def create(
        cls,
        payment_id: str,
        order_id: int,
        amount: Decimal,
        currency: str,
        user_id: int,
        payment_method: str,
        payment_gateway: str,
        error_message: str = "",
    ) -> "PaymentFailedEvent":
        """Create a new payment failed event."""
        import uuid

        return cls(
            payment_id=payment_id,
            order_id=order_id,
            amount=amount,
            currency=currency,
            user_id=user_id,
            payment_method=payment_method,
            payment_gateway=payment_gateway,
            error_message=error_message,
            event_id=str(uuid.uuid4()),
        )

    def to_dict(self) -> dict:
        """Convert event to dictionary for serialization."""
        return {
            "event_type": "PaymentFailed",
            "event_id": self.event_id,
            "payment_id": self.payment_id,
            "order_id": self.order_id,
            "amount": str(self.amount),
            "currency": self.currency,
            "user_id": self.user_id,
            "payment_method": self.payment_method,
            "payment_gateway": self.payment_gateway,
            "error_message": self.error_message,
            "timestamp": getattr(self, "_timestamp", None),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PaymentFailedEvent":
        """Create event from dictionary."""
        return cls(
            payment_id=data["payment_id"],
            order_id=data["order_id"],
            amount=Decimal(data["amount"]),
            currency=data["currency"],
            user_id=data["user_id"],
            payment_method=data["payment_method"],
            payment_gateway=data["payment_gateway"],
            error_message=data.get("error_message", ""),
            event_id=data["event_id"],
        )


@dataclass
class PaymentRefundedEvent:
    """Event triggered when a payment is refunded."""

    payment_id: str
    order_id: int
    amount: Decimal
    currency: str
    user_id: int
    payment_method: str
    payment_gateway: str
    refund_id: str = ""
    event_id: str = ""

    @classmethod
    def create(
        cls,
        payment_id: str,
        order_id: int,
        amount: Decimal,
        currency: str,
        user_id: int,
        payment_method: str,
        payment_gateway: str,
        refund_id: str = "",
    ) -> "PaymentRefundedEvent":
        """Create a new payment refunded event."""
        import uuid

        return cls(
            payment_id=payment_id,
            order_id=order_id,
            amount=amount,
            currency=currency,
            user_id=user_id,
            payment_method=payment_method,
            payment_gateway=payment_gateway,
            refund_id=refund_id,
            event_id=str(uuid.uuid4()),
        )

    def to_dict(self) -> dict:
        """Convert event to dictionary for serialization."""
        return {
            "event_type": "PaymentRefunded",
            "event_id": self.event_id,
            "payment_id": self.payment_id,
            "order_id": self.order_id,
            "amount": str(self.amount),
            "currency": self.currency,
            "user_id": self.user_id,
            "payment_method": self.payment_method,
            "payment_gateway": self.payment_gateway,
            "refund_id": self.refund_id,
            "timestamp": getattr(self, "_timestamp", None),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PaymentRefundedEvent":
        """Create event from dictionary."""
        return cls(
            payment_id=data["payment_id"],
            order_id=data["order_id"],
            amount=Decimal(data["amount"]),
            currency=data["currency"],
            user_id=data["user_id"],
            payment_method=data["payment_method"],
            payment_gateway=data["payment_gateway"],
            refund_id=data.get("refund_id", ""),
            event_id=data["event_id"],
        )