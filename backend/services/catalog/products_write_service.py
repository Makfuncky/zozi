"""Generated re-export shim (lazy).

Re-exports symbols from their canonical locations via PEP 562
__getattr__ so importing this module never triggers the load-time
controller/router imports that caused circular imports. Legacy
`from services.products_write_service import ...` keeps working;
the target module is imported only when the symbol is first accessed
(which happens at call time, after all modules are loaded)."""
from __future__ import annotations

import importlib
from typing import Callable, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session
import structlog
logger = structlog.get_logger(__name__)

_REEXPORTS: dict[str, tuple[str, str]] = {
    "create_flash_sale": ("controllers.flash_sale_controller", "create_flash_sale"),
    "delete_flash_sale": ("controllers.flash_sale_controller", "delete_flash_sale"),
    "update_flash_sale": ("controllers.flash_sale_controller", "update_flash_sale"),
    "create_product": ("controllers.products_controller", "create_product"),
    "update_product": ("controllers.products_controller", "update_product"),
    # Category CRUD is owned by services.catalog.category_service.
    "reorder_categories": ("services.catalog.category_service", "reorder_categories"),
    "create_category": ("services.catalog.category_service", "create_category"),
    "delete_category": ("services.catalog.category_service", "delete_category"),
    "update_category": ("services.catalog.category_service", "update_category"),
    # Real implementation in the reviews service (was incorrectly stubbed as a
    # refactor gap, breaking every caller).
    "update_product_rating": ("services.commerce.reviews_service", "recompute_product_rating"),
}

_MISSING: frozenset[str] = frozenset({
    "archive_product_reviews",
    "clear_product_carts",
    "clear_product_wishlists",
    "create_product_verification",
    "update_product_verification",
})


def _make_missing(name: str) -> Callable:
    def _f(*_a, **_k):
        raise NotImplementedError(
            f"'{__name__}.{name}' is not implemented (refactor gap)")
    _f.__name__ = name
    return _f


def _soft_delete_by_product(db: Session, model, product_id: int) -> int:
    """Soft-delete every (non-deleted) row of *model* for *product_id*."""
    from utils.datetime_utils import utcnow

    updated = (
        db.query(model)
        .filter(model.product_id == product_id, model.is_deleted.is_(False))
        .update(
            {model.is_deleted: True, model.deleted_at: utcnow()},
            synchronize_session=False,
        )
    )
    db.commit()
    return updated


def clear_product_carts(db: Session, product_id: int) -> int:
    """Remove (soft-delete) all cart items for a product during cascade delete."""
    from data.models import CartItem

    return _soft_delete_by_product(db, CartItem, product_id)


def clear_product_wishlists(db: Session, product_id: int) -> int:
    """Remove (soft-delete) all wishlist items for a product during cascade delete."""
    from data.models import WishlistItem

    return _soft_delete_by_product(db, WishlistItem, product_id)


def archive_product_reviews(db: Session, product_id: int) -> int:
    """Soft-delete a product's reviews, preserving the data history."""
    from data.models import Review

    return _soft_delete_by_product(db, Review, product_id)


# ── cascade writes for product deletion (no commit; caller owns the txn) ─────

def purge_product_cart_items(db: Session, product_id: int) -> int:
    """Remove every cart row referencing *product_id*. Caller commits."""
    from data.models import CartItem

    return (
        db.query(CartItem)
        .filter(CartItem.product_id == product_id)
        .delete(synchronize_session=False)
    )


def purge_product_wishlist_items(db: Session, product_id: int) -> int:
    """Remove every wishlist row referencing *product_id*. Caller commits."""
    from data.models import Wishlist

    return (
        db.query(Wishlist)
        .filter(Wishlist.product_id == product_id)
        .delete(synchronize_session=False)
    )


def soft_delete_product_reviews(db: Session, product_id: int) -> int:
    """Flag a product's live reviews as deleted. Caller commits."""
    from data.models import Review

    return (
        db.query(Review)
        .filter(Review.product_id == product_id, Review.is_deleted == False)  # noqa: E712
        .update({"is_deleted": True}, synchronize_session=False)
    )


def create_product_verification(
    db: Session,
    *,
    product_id: int,
    order_id: Optional[int] = None,
    shipment_id: Optional[int] = None,
    verified_by: Optional[int] = None,
    verification_type: Optional[str] = None,
    result: Optional[str] = None,
    expected_specs: Optional[str] = None,
    actual_specs: Optional[str] = None,
    discrepancies: Optional[str] = None,
    scan_code: Optional[str] = None,
    image_urls: Optional[str] = None,
    notes: Optional[str] = None,
):
    """Persist a new :class:`ProductVerification` row and return it."""
    from data.models import ProductVerification

    verification = ProductVerification(
        product_id=product_id,
        order_id=order_id,
        shipment_id=shipment_id,
        verified_by=verified_by,
        verification_type=verification_type,
        result=result,
        expected_specs=expected_specs,
        actual_specs=actual_specs,
        discrepancies=discrepancies,
        scan_code=scan_code,
        image_urls=image_urls,
        notes=notes,
    )
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return verification


def update_product_verification(db: Session, verification, updates: dict):
    """Apply *updates* to an existing verification row and return it."""
    for key, value in updates.items():
        setattr(verification, key, value)
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return verification

def __getattr__(name: str):
    spec = _REEXPORTS.get(name)
    if spec is not None:
        module = importlib.import_module(spec[0])
        value = getattr(module, spec[1])
        globals()[name] = value
        return value
    if name in _MISSING:
        value = _make_missing(name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def __dir__():
    return sorted(set(globals()) | set(_REEXPORTS) | set(_MISSING))
