"""Finance domain — typed cross-domain events (Law 3).

Cross-domain **writes** travel exclusively through ``events.py`` /
``subscribers.py``. Each event is a frozen dataclass with an event-type
discriminator, a UTC ``occurred_at`` timestamp, and a ``serialize()``
method so the event bus can emit them to subscribers.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

# Canonical event type constants (shared contract)
EVENT_INVOICE_ISSUED = "finance.invoice.issued"
EVENT_PAYMENT_PROCESSED = "finance.payment.processed"
EVENT_PAYOUT_COMPLETED = "finance.payout.completed"
EVENT_COMMISSION_CALCULATED = "finance.commission.calculated"

# ── base ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class FinanceEvent:
    """Base class for all finance-domain events."""

    event_type: str = field(init=False)
    event_id: str = field(default_factory=lambda: str(uuid4()), init=False)
    occurred_at: datetime = field(
        default_factory=lambda: datetime.utcnow(), init=False
    )

    def serialize(self) -> Dict[str, Any]:
        """Plain-dict form for the event bus."""
        d = asdict(self)
        d["occurred_at"] = self.occurred_at.isoformat()
        return d

# ── invoice events ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class InvoiceIssued(FinanceEvent):
    invoice_id: int = 0
    order_id: Optional[int] = None
    amount: str = ""
    currency: str = ""
    event_type: str = field(default=EVENT_INVOICE_ISSUED, init=False)

# ── payment events ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PaymentProcessed(FinanceEvent):
    payment_id: int = 0
    order_id: Optional[int] = None
    amount: str = ""
    currency: str = ""
    gateway: str = ""
    event_type: str = field(default=EVENT_PAYMENT_PROCESSED, init=False)

# ── payout events ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PayoutCompleted(FinanceEvent):
    payout_id: int = 0
    recipient_type: str = ""
    recipient_id: Optional[int] = None
    amount: str = ""
    currency: str = ""
    event_type: str = field(default=EVENT_PAYOUT_COMPLETED, init=False)

# ── commission events ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class CommissionCalculated(FinanceEvent):
    commission_id: int = 0
    order_id: Optional[int] = None
    supplier_id: Optional[int] = None
    amount: str = ""
    currency: str = ""
    event_type: str = field(default=EVENT_COMMISSION_CALCULATED, init=False)

# ── publish helpers (integrate with canonical event bus) ──────────────────

def publish_invoice_issued(invoice_id: int, amount: str, currency: str, order_id: Optional[int] = None) -> None:
    """Publish an InvoiceIssued event to the canonical event bus."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = InvoiceIssued(invoice_id=invoice_id, order_id=order_id, amount=amount, currency=currency)
        publish(EVENT_INVOICE_ISSUED, event.serialize())
    except Exception:
        pass  # Event publishing is best-effort

def publish_payment_processed(payment_id: int, amount: str, currency: str, gateway: str, order_id: Optional[int] = None) -> None:
    """Publish a PaymentProcessed event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = PaymentProcessed(payment_id=payment_id, order_id=order_id, amount=amount, currency=currency, gateway=gateway)
        publish(EVENT_PAYMENT_PROCESSED, event.serialize())
    except Exception:
        pass

def publish_payout_completed(payout_id: int, recipient_type: str, amount: str, currency: str, recipient_id: Optional[int] = None) -> None:
    """Publish a PayoutCompleted event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = PayoutCompleted(payout_id=payout_id, recipient_type=recipient_type, recipient_id=recipient_id, amount=amount, currency=currency)
        publish(EVENT_PAYOUT_COMPLETED, event.serialize())
    except Exception:
        pass

def publish_commission_calculated(commission_id: int, amount: str, currency: str, order_id: Optional[int] = None, supplier_id: Optional[int] = None) -> None:
    """Publish a CommissionCalculated event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = CommissionCalculated(commission_id=commission_id, order_id=order_id, supplier_id=supplier_id, amount=amount, currency=currency)
        publish(EVENT_COMMISSION_CALCULATED, event.serialize())
    except Exception:
        pass

__all__ = [
    # Event type constants
    "EVENT_INVOICE_ISSUED",
    "EVENT_PAYMENT_PROCESSED",
    "EVENT_PAYOUT_COMPLETED",
    "EVENT_COMMISSION_CALCULATED",
    # Event classes
    "FinanceEvent",
    "InvoiceIssued",
    "PaymentProcessed",
    "PayoutCompleted",
    "CommissionCalculated",
    # Publish helpers
    "publish_invoice_issued",
    "publish_payment_processed",
    "publish_payout_completed",
    "publish_commission_calculated",
]
