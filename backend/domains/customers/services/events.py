"""Customers domain — typed cross-domain events (Law 3).

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
EVENT_CUSTOMER_REGISTERED = "customers.customer.registered"
EVENT_REVIEW_SUBMITTED = "customers.review.submitted"
EVENT_COINS_EARNED = "customers.coins.earned"
EVENT_COINS_REDEEMED = "customers.coins.redeemed"

# ── base ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CustomersEvent:
    """Base class for all customers-domain events."""

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

# ── customer events ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class CustomerRegistered(CustomersEvent):
    user_id: int = 0
    email: str = ""
    country_code: str = ""
    referral_code: Optional[str] = None
    event_type: str = field(default=EVENT_CUSTOMER_REGISTERED, init=False)

@dataclass(frozen=True)
class ReviewSubmitted(CustomersEvent):
    review_id: int = 0
    product_id: int = 0
    user_id: int = 0
    rating: int = 0
    event_type: str = field(default=EVENT_REVIEW_SUBMITTED, init=False)

@dataclass(frozen=True)
class CoinsEarned(CustomersEvent):
    user_id: int = 0
    amount: int = 0
    reason: str = ""
    reference_id: Optional[int] = None
    event_type: str = field(default=EVENT_COINS_EARNED, init=False)

@dataclass(frozen=True)
class CoinsRedeemed(CustomersEvent):
    user_id: int = 0
    amount: int = 0
    reason: str = ""
    order_id: Optional[int] = None
    event_type: str = field(default=EVENT_COINS_REDEEMED, init=False)

# ── publish helpers (integrate with canonical event bus) ──────────────────

def publish_customer_registered(user_id: int, email: str, country_code: str, referral_code: Optional[str] = None) -> None:
    """Publish a CustomerRegistered event to the canonical event bus."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = CustomerRegistered(user_id=user_id, email=email, country_code=country_code, referral_code=referral_code)
        publish(EVENT_CUSTOMER_REGISTERED, event.serialize())
    except Exception:
        pass  # Event publishing is best-effort

def publish_review_submitted(review_id: int, product_id: int, user_id: int, rating: int) -> None:
    """Publish a ReviewSubmitted event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = ReviewSubmitted(review_id=review_id, product_id=product_id, user_id=user_id, rating=rating)
        publish(EVENT_REVIEW_SUBMITTED, event.serialize())
    except Exception:
        pass

def publish_coins_earned(user_id: int, amount: int, reason: str, reference_id: Optional[int] = None) -> None:
    """Publish a CoinsEarned event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = CoinsEarned(user_id=user_id, amount=amount, reason=reason, reference_id=reference_id)
        publish(EVENT_COINS_EARNED, event.serialize())
    except Exception:
        pass

def publish_coins_redeemed(user_id: int, amount: int, reason: str, order_id: Optional[int] = None) -> None:
    """Publish a CoinsRedeemed event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = CoinsRedeemed(user_id=user_id, amount=amount, reason=reason, order_id=order_id)
        publish(EVENT_COINS_REDEEMED, event.serialize())
    except Exception:
        pass

__all__ = [
    # Event type constants
    "EVENT_CUSTOMER_REGISTERED",
    "EVENT_REVIEW_SUBMITTED",
    "EVENT_COINS_EARNED",
    "EVENT_COINS_REDEEMED",
    # Event classes
    "CustomersEvent",
    "CustomerRegistered",
    "ReviewSubmitted",
    "CoinsEarned",
    "CoinsRedeemed",
    # Publish helpers
    "publish_customer_registered",
    "publish_review_submitted",
    "publish_coins_earned",
    "publish_coins_redeemed",
]
