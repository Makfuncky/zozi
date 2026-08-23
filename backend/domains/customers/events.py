"""customers domain - AXIS 2 event surface (Law 3: cross-domain writes via events).

The customers domain owns the ``customer``-schema entities (addresses, cart,
wishlist, referrals, reviews). It publishes notifications when those entities
change so downstream domains (orders, governance, comms) may react.

Transport is the sanctioned in-process ``event_bus`` (circuit-exempt data layer).
"""

from __future__ import annotations

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
