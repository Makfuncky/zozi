"""payments domain events.

Per Law 3 (cross-domain writes only via events), the payments domain emits
events that other domains subscribe to. Consumers (orders, finance, comms)
react to these but never read payments state directly — they go through
``domains/payments/ports.py`` (Law 3 — cross-domain reads only via ports).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, Optional


@dataclass
class PaymentEvent:
    """Base class for all payments domain events."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    meta: Dict[str, Any] = field(default_factory=dict)


# ── Payment lifecycle ────────────────────────────────────────────────────────


@dataclass
class PaymentAuthorized(PaymentEvent):
    """A payment intent was authorized by the gateway but not yet captured."""

    payment_id: int = 0
    order_id: int = 0
    amount: Decimal = Decimal("0")
    currency: str = "AED"
    country_code: str = ""
    provider: str = ""
    provider_intent_id: Optional[str] = None


@dataclass
class PaymentCaptured(PaymentEvent):
    """A payment intent was captured (funds settled)."""

    payment_id: int = 0
    order_id: int = 0
    amount: Decimal = Decimal("0")
    currency: str = "AED"
    country_code: str = ""
    provider: str = ""
    provider_intent_id: Optional[str] = None


@dataclass
class PaymentFailed(PaymentEvent):
    """A payment intent failed (gateway decline / error)."""

    payment_id: int = 0
    order_id: int = 0
    amount: Decimal = Decimal("0")
    currency: str = "AED"
    country_code: str = ""
    provider: str = ""
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class PaymentRefunded(PaymentEvent):
    """A payment was refunded (full or partial)."""

    payment_id: int = 0
    refund_id: int = 0
    order_id: int = 0
    amount: Decimal = Decimal("0")
    currency: str = "AED"
    country_code: str = ""
    provider: str = ""
    reason: Optional[str] = None
