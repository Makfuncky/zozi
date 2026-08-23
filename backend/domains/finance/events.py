"""finance domain events.

Finance is a *publishing* domain: when financial state changes it emits events
that other domains may subscribe to (Law 3 — cross-domain writes only via
events). Events are plain dataclass-like objects; the bus is
``infrastructure.messaging.events.event_publisher.EventPublisher`` (which keys
listeners by event *type*).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, Optional


@dataclass
class FinanceEvent:
    """Base class for all finance domain events."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    meta: Dict[str, Any] = field(default_factory=dict)


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
