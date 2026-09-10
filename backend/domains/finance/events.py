"""finance domain events.

Finance is a *publishing* domain: when financial state changes it emits events
that other domains may subscribe to (Law 3 — cross-domain writes only via
events). Events are plain dataclass-like objects; the bus is
``infrastructure.messaging.events.event_publisher.EventPublisher`` (which keys
listeners by event *type*).
"""


import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, Optional


@dataclass
class FinanceEvent:
    """Base class for all finance domain events."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))


# ── Journal / ledger events ─────────────────────────────────────────────────


@dataclass
class JournalEntryPosted(FinanceEvent):
    """A journal entry was posted to the general ledger."""

    journal_entry_id: int = 0
    reference_number: str = ""
    country_code: str = ""
    amount: Decimal = Decimal("0")
    posted_by: Optional[int] = None


@dataclass
class JournalEntryReversed(FinanceEvent):
    """A journal entry was reversed."""

    journal_entry_id: int = 0
    reversal_entry_id: int = 0
    reason: str = ""
    reversed_by: Optional[int] = None


# ── Payout events ────────────────────────────────────────────────────────────


@dataclass
class PayoutCreated(FinanceEvent):
    """A payout was created."""

    payout_id: int = 0
    entity_type: str = ""
    entity_id: int = 0
    amount: Decimal = Decimal("0")
    currency: str = "USD"
    country_code: str = ""
    created_by: Optional[int] = None


@dataclass
class PayoutApproved(FinanceEvent):
    """A payout was approved (maker-checker)."""

    payout_id: int = 0
    approved_by: Optional[int] = None
    country_code: str = ""


@dataclass
class PayoutRejected(FinanceEvent):
    """A payout was rejected."""

    payout_id: int = 0
    rejected_by: Optional[int] = None
    reason: str = ""
    country_code: str = ""


@dataclass
class PayoutDispatched(FinanceEvent):
    """A payout batch was dispatched for settlement."""

    batch_id: int = 0
    total_amount: Decimal = Decimal("0")
    item_count: int = 0
    dispatched_by: Optional[int] = None
    country_code: str = ""


# ── Invoice events ───────────────────────────────────────────────────────────


@dataclass
class InvoiceCreated(FinanceEvent):
    """An invoice was created."""

    invoice_id: int = 0
    order_id: int = 0
    supplier_id: Optional[int] = None
    total_amount: Decimal = Decimal("0")
    currency: str = "USD"
    country_code: str = ""


@dataclass
class InvoicePaid(FinanceEvent):
    """An invoice was marked as paid."""

    invoice_id: int = 0
    paid_amount: Decimal = Decimal("0")
    paid_by: Optional[int] = None
    country_code: str = ""


# ── Period close events ──────────────────────────────────────────────────────


@dataclass
class FiscalPeriodClosed(FinanceEvent):
    """A fiscal period was closed."""

    period_id: int = 0
    country_code: str = ""
    period_year: int = 0
    period_month: int = 0
    closed_by: Optional[int] = None


# ── Refund events ────────────────────────────────────────────────────────────


@dataclass
class RefundPosted(FinanceEvent):
    """A refund was posted to the refund ledger."""

    refund_id: int = 0
    order_id: int = 0
    customer_refund_amount: Decimal = Decimal("0")
    currency: str = "USD"
    country_code: str = ""
    posted_by: Optional[int] = None


# ── Commission events ────────────────────────────────────────────────────────


@dataclass
class CommissionAccrued(FinanceEvent):
    """Commission was accrued for an order."""

    commission_id: int = 0
    order_id: int = 0
    supplier_id: Optional[int] = None
    commission_amount: Decimal = Decimal("0")
    applied_rate: Decimal = Decimal("0")
    currency: str = "USD"
    country_code: str = ""

# imports merged from services/
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

# constants merged from services/
EVENT_COMMISSION_CALCULATED = "finance.commission.calculated"
EVENT_INVOICE_ISSUED = "finance.invoice.issued"
EVENT_PAYMENT_PROCESSED = "finance.payment.processed"
EVENT_PAYOUT_COMPLETED = "finance.payout.completed"

# base classes merged from services/
class CommissionCalculated(FinanceEvent):
    commission_id: int = 0
    order_id: Optional[int] = None
    supplier_id: Optional[int] = None
    amount: str = ""
    currency: str = ""
    event_type: str = field(default=EVENT_COMMISSION_CALCULATED, init=False)
class InvoiceIssued(FinanceEvent):
    invoice_id: int = 0
    order_id: Optional[int] = None
    amount: str = ""
    currency: str = ""
    event_type: str = field(default=EVENT_INVOICE_ISSUED, init=False)
class PaymentProcessed(FinanceEvent):
    payment_id: int = 0
    order_id: Optional[int] = None
    amount: str = ""
    currency: str = ""
    gateway: str = ""
    event_type: str = field(default=EVENT_PAYMENT_PROCESSED, init=False)
class PayoutCompleted(FinanceEvent):
    payout_id: int = 0
    recipient_type: str = ""
    recipient_id: Optional[int] = None
    amount: str = ""
    currency: str = ""
    event_type: str = field(default=EVENT_PAYOUT_COMPLETED, init=False)

# functions merged from services/
def publish_commission_calculated(commission_id: int, amount: str, currency: str, order_id: Optional[int] = None, supplier_id: Optional[int] = None) -> None:
    """Publish a CommissionCalculated event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = CommissionCalculated(commission_id=commission_id, order_id=order_id, supplier_id=supplier_id, amount=amount, currency=currency)
        publish(EVENT_COMMISSION_CALCULATED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish CommissionCalculated event: %s", exc)
def publish_invoice_issued(invoice_id: int, amount: str, currency: str, order_id: Optional[int] = None) -> None:
    """Publish an InvoiceIssued event to the canonical event bus."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = InvoiceIssued(invoice_id=invoice_id, order_id=order_id, amount=amount, currency=currency)
        publish(EVENT_INVOICE_ISSUED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish InvoiceIssued event: %s", exc)
def publish_payment_processed(payment_id: int, amount: str, currency: str, gateway: str, order_id: Optional[int] = None) -> None:
    """Publish a PaymentProcessed event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = PaymentProcessed(payment_id=payment_id, order_id=order_id, amount=amount, currency=currency, gateway=gateway)
        publish(EVENT_PAYMENT_PROCESSED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish PaymentProcessed event: %s", exc)
def publish_payout_completed(payout_id: int, recipient_type: str, amount: str, currency: str, recipient_id: Optional[int] = None) -> None:
    """Publish a PayoutCompleted event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = PayoutCompleted(payout_id=payout_id, recipient_type=recipient_type, recipient_id=recipient_id, amount=amount, currency=currency)
        publish(EVENT_PAYOUT_COMPLETED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish PayoutCompleted event: %s", exc)
