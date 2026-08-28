"""customers domain - sanctioned cross-domain READ surface (ports).

Per ARCHITECTURE_DIAGRAM.md Law 3, cross-domain *reads* may ONLY happen through a
publishing domain's ``ports.py``. Other domains import these functions instead
of importing ``domains.customers.models`` or ``domains.customers.services`` directly.

These are pure read helpers: no writes, no business decisions, no permission
checks (callers remain responsible for feature gating via ``rbac``).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

# Cross-domain re-exports (sanctioned READ surface per Law 3).
# Shipping quotes are owned by the orders domain; re-exported here so the
# customer module routers import them from customers.ports instead of
# directly from domains.orders.services.
from domains.orders.ports import CartShippingQuoteRequest, get_cart_shipping_quote


def get_may_you_like(db: Session, user_id: int, limit: int = 8) -> list:
    """Sanctioned cross-domain read: personalized product recommendations."""
    from domains.customers.services.recommendations.recommendation_service import get_may_you_like as _svc
    return _svc(db, user_id, limit=limit)


def get_last_seen(db: Session, user_id: int, limit: int = 12) -> list:
    """Sanctioned cross-domain read: recently viewed products."""
    from domains.customers.services.recommendations.recommendation_service import get_last_seen as _svc
    return _svc(db, user_id, limit=limit)


# ── Commerce service functions (sanctioned cross-domain delegation) ─────────
# Thin wrappers so module routers import from customers.ports instead of
# directly from domains.customers.services.

def unset_other_default_addresses(db: Session, user_id: int, address_id: Optional[int] = None) -> int:
    """Sanctioned cross-domain write: unset other default addresses."""
    from domains.customers.services.commerce_write_service import unset_other_default_addresses as _svc
    return _svc(db, user_id, address_id)


def list_user_addresses(db: Session, user_id: int, limit: int = 100, cursor: int | None = None) -> list:
    """Sanctioned cross-domain read: list user addresses."""
    from domains.customers.services.commerce_read_service import list_user_addresses as _svc
    return _svc(db, user_id, limit=limit, cursor=cursor)


def get_user_address(db: Session, address_id: int, user_id: int):
    """Sanctioned cross-domain read: get a single user address."""
    from domains.customers.services.commerce_read_service import get_user_address as _svc
    return _svc(db, address_id, user_id)


# ── Zozi Coins (sanctioned cross-domain delegation) ─────────────────────────
# Thin wrappers so module routers import from customers.ports instead of
# directly from domains.customers.services.coins.zozi_coins_service.

def get_coin_summary(db: Session, user_id: int):
    """Sanctioned cross-domain read: get a customer's coin balance and history."""
    from domains.customers.services.coins.zozi_coins_service import get_coin_summary as _svc
    return _svc(db, user_id)


def redeem_coins(db: Session, user_id: int, points: int, reason: str = "redemption"):
    """Sanctioned cross-domain write: redeem coins from a customer's balance."""
    from domains.customers.services.coins.zozi_coins_service import redeem_coins as _svc
    return _svc(db, user_id, points, reason=reason)


# ── Reviews (sanctioned cross-domain delegation) ─────────────────────────────
# Thin wrappers so module routers import from customers.ports instead of
# directly from domains.customers.services.reviews_service.

def get_product_reviews(db: Session, product_id: int):
    """Sanctioned cross-domain read: list reviews for a product."""
    from domains.customers.services.reviews_service import get_product_reviews as _svc
    return _svc(db, product_id)


def review_product_exists(db: Session, product_id: int) -> bool:
    """Sanctioned cross-domain read: check if a product exists for reviews."""
    from domains.customers.services.reviews_service import product_exists as _svc
    return _svc(db, product_id)


def find_existing_review(db: Session, product_id: int, user_id: int):
    """Sanctioned cross-domain read: find an existing review by user/product."""
    from domains.customers.services.reviews_service import find_existing_review as _svc
    return _svc(db, product_id, user_id)


def create_review(db: Session, **kwargs):
    """Sanctioned cross-domain write: create a product review."""
    from domains.customers.services.reviews_service import create_review as _svc
    return _svc(db, **kwargs)


def soft_delete_review(db: Session, review) -> None:
    """Sanctioned cross-domain write: soft-delete a review."""
    from domains.customers.services.reviews_service import soft_delete_review as _svc
    return _svc(db, review)


def delete_review_by_user(db: Session, review_id: int, user_id: int, user_role: str) -> dict:
    """Sanctioned cross-domain write: delete a review scoped to user/role."""
    from domains.customers.services.reviews_service import delete_review_by_user as _svc
    return _svc(db, review_id, user_id, user_role)


# ── Wishlist (sanctioned cross-domain delegation) ────────────────────────────
# Thin wrappers so module routers import from customers.ports instead of
# directly from domains.customers.services.wishlist_*_service.

def get_user_wishlist(db: Session, user_id: int):
    """Sanctioned cross-domain read: list a user's wishlist items."""
    from domains.customers.services.wishlist_read_service import get_user_wishlist as _svc
    return _svc(db, user_id)


def get_wishlist_item_by_product(db: Session, user_id: int, product_id: int):
    """Sanctioned cross-domain read: get a wishlist entry for a product."""
    from domains.customers.services.wishlist_read_service import get_wishlist_item_by_product as _svc
    return _svc(db, user_id, product_id)


def wishlist_product_exists(db: Session, product_id: int) -> bool:
    """Sanctioned cross-domain read: check if a product exists for wishlist."""
    from domains.customers.services.wishlist_read_service import product_exists as _svc
    return _svc(db, product_id)


def create_wishlist_item(db: Session, user_id: int, product_id: int):
    """Sanctioned cross-domain write: add a product to a user's wishlist."""
    from domains.customers.services.wishlist_write_service import create_wishlist_item as _svc
    return _svc(db, user_id, product_id)


def delete_wishlist_item(db: Session, item) -> None:
    """Sanctioned cross-domain write: remove a wishlist entry."""
    from domains.customers.services.wishlist_write_service import delete_wishlist_item as _svc
    return _svc(db, item)


__all__ = [
    "CartShippingQuoteRequest",
    "get_cart_shipping_quote",
    "get_may_you_like",
    "get_last_seen",
    "unset_other_default_addresses",
    "list_user_addresses",
    "get_user_address",
    "get_coin_summary",
    "redeem_coins",
    "get_product_reviews",
    "review_product_exists",
    "find_existing_review",
    "create_review",
    "soft_delete_review",
    "delete_review_by_user",
    "get_user_wishlist",
    "get_wishlist_item_by_product",
    "wishlist_product_exists",
    "create_wishlist_item",
    "delete_wishlist_item",
]

# --- Lazy service exports (Law 3 sanctioned cross-domain surface) ---
# Cross-domain consumers import these from ports instead of reaching
# into the services tree directly.
_LAZY_SERVICE_EXPORTS: dict[str, tuple[str, str]] = {
    "get_user_address": ("domains.customers.services.commerce_read_service", "get_user_address"),
    "list_user_addresses": ("domains.customers.services.commerce_read_service", "list_user_addresses"),
    "create_address": ("domains.customers.services.commerce_write_service", "create_address"),
    "delete_address": ("domains.customers.services.commerce_write_service", "delete_address"),
    "set_default_address": ("domains.customers.services.commerce_write_service", "set_default_address"),
    "unset_other_default_addresses": ("domains.customers.services.commerce_write_service", "unset_other_default_addresses"),
    "update_address": ("domains.customers.services.commerce_write_service", "update_address"),
    "_normalize_address_payload": ("domains.customers.services.customer_router_service", "_normalize_address_payload"),
    "_serialize_address": ("domains.customers.services.customer_router_service", "_serialize_address"),
    "ConnectionManager": ("domains.customers.services.public_comms_status_service", "ConnectionManager"),
    "UserConnectionManager": ("domains.customers.services.public_comms_status_service", "UserConnectionManager"),
    "_decode_ws_token": ("domains.customers.services.public_comms_status_service", "_decode_ws_token"),
    "websocket_chat": ("domains.customers.services.public_comms_status_service", "websocket_chat"),
}
import importlib

def __getattr__(name: str):
    if name in _LAZY_SERVICE_EXPORTS:
        module_path, symbol = _LAZY_SERVICE_EXPORTS[name]
        mod = importlib.import_module(module_path)
        value = getattr(mod, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

