"""customers domain - AXIS 2 event surface (Law 3: cross-domain writes via events).

The customers domain owns the ``customer``-schema entities (addresses, cart,
wishlist, referrals, reviews). It publishes notifications when those entities
change so downstream domains (orders, governance, comms) may react.

Transport is the sanctioned in-process ``event_bus`` (circuit-exempt data layer).
"""


from infrastructure.messaging.events.event_bus import publish

# --- notifications the customers domain emits after a write (downstream reacts) ---
EVENT_CUSTOMER_ADDRESS_CREATED = "customers.address.created"
EVENT_CART_ITEM_ADDED = "customers.cart.item_added"
EVENT_CART_ITEM_REMOVED = "customers.cart.item_removed"
EVENT_WISHLIST_ITEM_ADDED = "customers.wishlist.item_added"
EVENT_WISHLIST_ITEM_REMOVED = "customers.wishlist.item_removed"
EVENT_REFERRAL_CREATED = "customers.referral.created"
EVENT_REVIEW_SUBMITTED = "customers.review.submitted"
EVENT_RETURN_REQUESTED = "customers.return.requested"


def publish_customer_address_created(address_id: int, user_id: int, country_code: str | None = None) -> None:
    publish(EVENT_CUSTOMER_ADDRESS_CREATED, {"address_id": address_id, "user_id": user_id, "country_code": country_code})


def publish_cart_item_added(user_id: int, product_id: int, quantity: int) -> None:
    publish(EVENT_CART_ITEM_ADDED, {"user_id": user_id, "product_id": product_id, "quantity": quantity})


def publish_cart_item_removed(user_id: int, product_id: int) -> None:
    publish(EVENT_CART_ITEM_REMOVED, {"user_id": user_id, "product_id": product_id})


def publish_wishlist_item_added(user_id: int, product_id: int) -> None:
    publish(EVENT_WISHLIST_ITEM_ADDED, {"user_id": user_id, "product_id": product_id})


def publish_wishlist_item_removed(user_id: int, product_id: int) -> None:
    publish(EVENT_WISHLIST_ITEM_REMOVED, {"user_id": user_id, "product_id": product_id})


def publish_referral_created(referrer_id: int, referred_id: int, referral_code: str) -> None:
    publish(EVENT_REFERRAL_CREATED, {"referrer_id": referrer_id, "referred_id": referred_id, "referral_code": referral_code})


def publish_review_submitted(review_id: int, product_id: int, user_id: int) -> None:
    publish(EVENT_REVIEW_SUBMITTED, {"review_id": review_id, "product_id": product_id, "user_id": user_id})


def publish_return_requested(return_id: int, order_id: int, user_id: int) -> None:
    publish(EVENT_RETURN_REQUESTED, {"return_id": return_id, "order_id": order_id, "user_id": user_id})


__all__ = [
    "EVENT_CUSTOMER_ADDRESS_CREATED",
    "EVENT_CART_ITEM_ADDED",
    "EVENT_CART_ITEM_REMOVED",
    "EVENT_WISHLIST_ITEM_ADDED",
    "EVENT_WISHLIST_ITEM_REMOVED",
    "EVENT_REFERRAL_CREATED",
    "EVENT_REVIEW_SUBMITTED",
    "EVENT_RETURN_REQUESTED",
    "publish_customer_address_created",
    "publish_cart_item_added",
    "publish_cart_item_removed",
    "publish_wishlist_item_added",
    "publish_wishlist_item_removed",
    "publish_referral_created",
    "publish_review_submitted",
    "publish_return_requested",
]

# imports merged from services/
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

# constants merged from services/
EVENT_COINS_EARNED = "customers.coins.earned"
EVENT_COINS_REDEEMED = "customers.coins.redeemed"
EVENT_CUSTOMER_REGISTERED = "customers.customer.registered"

# base classes merged from services/
class CustomersEvent:
    """Base class for all customers-domain events."""

    event_type: str = field(init=False)
    event_id: str = field(default_factory=lambda: str(uuid4()), init=False)
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc), init=False
    )

    def serialize(self) -> Dict[str, Any]:
        """Plain-dict form for the event bus."""
        d = asdict(self)
        d["occurred_at"] = self.occurred_at.isoformat()
        return d

# derived classes merged from services/
class CoinsEarned(CustomersEvent):
    user_id: int = 0
    amount: int = 0
    reason: str = ""
    reference_id: Optional[int] = None
    event_type: str = field(default=EVENT_COINS_EARNED, init=False)
class CoinsRedeemed(CustomersEvent):
    user_id: int = 0
    amount: int = 0
    reason: str = ""
    order_id: Optional[int] = None
    event_type: str = field(default=EVENT_COINS_REDEEMED, init=False)
class CustomerRegistered(CustomersEvent):
    user_id: int = 0
    email: str = ""
    country_code: str = ""
    referral_code: Optional[str] = None
    event_type: str = field(default=EVENT_CUSTOMER_REGISTERED, init=False)
class ReviewSubmitted(CustomersEvent):
    review_id: int = 0
    product_id: int = 0
    user_id: int = 0
    rating: int = 0
    event_type: str = field(default=EVENT_REVIEW_SUBMITTED, init=False)

# functions merged from services/
def publish_coins_earned(user_id: int, amount: int, reason: str, reference_id: Optional[int] = None) -> None:
    """Publish a CoinsEarned event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = CoinsEarned(user_id=user_id, amount=amount, reason=reason, reference_id=reference_id)
        publish(EVENT_COINS_EARNED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish CoinsEarned event: %s", exc)
def publish_coins_redeemed(user_id: int, amount: int, reason: str, order_id: Optional[int] = None) -> None:
    """Publish a CoinsRedeemed event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = CoinsRedeemed(user_id=user_id, amount=amount, reason=reason, order_id=order_id)
        publish(EVENT_COINS_REDEEMED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish CoinsRedeemed event: %s", exc)
def publish_customer_registered(user_id: int, email: str, country_code: str, referral_code: Optional[str] = None) -> None:
    """Publish a CustomerRegistered event to the canonical event bus."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = CustomerRegistered(user_id=user_id, email=email, country_code=country_code, referral_code=referral_code)
        publish(EVENT_CUSTOMER_REGISTERED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish CustomerRegistered event: %s", exc)
