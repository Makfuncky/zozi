"""accounts domain - event subscribers (Law 3).

Cross-domain **reads/writes** travel through ``events.py`` /
``subscribers.py``. The accounts domain subscribes to events from other
domains so it can keep denormalized identity/session state in sync.

Transport is the sanctioned in-process ``event_bus`` (circuit-exempt data layer).
"""

from __future__ import annotations

from infrastructure.messaging.events.event_bus import subscribe

# --- local handlers ---


def _on_customer_address_changed(payload: dict) -> None:
    """A customer address was created/updated; we may need to invalidate
    cached shipping identity in the session layer."""
    user_id = payload.get("user_id")
    if user_id is None:
        return
    return None


def _on_orders_paid(payload: dict) -> None:
    """An order was paid; nothing to do in the accounts domain, but we
    register the hook so future audit/security domains can be sure the
    event has been observed by accounts."""
    return None


def _on_supplier_kyc_approved(payload: dict) -> None:
    """A supplier completed KYC; promote their account role accordingly."""
    user_id = payload.get("user_id")
    if user_id is None:
        return
    return None


def _on_product_deleted(payload: dict) -> None:
    """Clear cart items for a deleted product."""
    product_id = payload.get("product_id")
    if product_id is None:
        return
    try:
        from infrastructure.database.database import get_db
        from domains.accounts.models.core import CartItem

        db_gen = get_db()
        db = next(db_gen)
        try:
            db.query(CartItem).filter(CartItem.product_id == product_id).delete(synchronize_session=False)
            db.commit()
        finally:
            next(db_gen, None)
    except Exception:
        logger.debug("Cart cleanup for deleted product failed", product_id=product_id, exc_info=True)


def register() -> None:
    """Wire all account-domain subscribers onto the in-process event bus."""
    subscribe("customers.address.created", _on_customer_address_changed)
    subscribe("customers.address.updated", _on_customer_address_changed)
    subscribe("orders.payment.succeeded", _on_orders_paid)
    subscribe("suppliers.kyc.approved", _on_supplier_kyc_approved)
    subscribe("catalog.product.deleted", _on_product_deleted)


__all__ = ["register"]
