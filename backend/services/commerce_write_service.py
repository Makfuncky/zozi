"""Commerce write service — real implementations for the customer address book,
plus lazy PEP 562 re-exports for wishlist/review helpers that live in their
canonical modules.

The address-book functions here are the single source of truth for persisting
``data.models.Address`` rows. They accept flat keyword arguments so the
first-party ``routers/addresses.py`` layer (which normalises payloads itself)
can call them directly without an extra translation layer.
"""
from __future__ import annotations

import importlib
from typing import Optional

from sqlalchemy.orm import Session

from data.models import Address
import structlog
logger = structlog.get_logger(__name__)


def unset_other_default_addresses(
    db: Session, user_id: int, address_id: Optional[int] = None
) -> int:
    """Clear the ``is_default`` flag on every other address for *user_id*.

    Used when a new address is promoted to default (no *address_id*) or when an
    existing address is set default (exclude *address_id*).
    """
    query = db.query(Address).filter(
        Address.user_id == user_id,
        Address.is_default.is_(True),
        Address.is_deleted.is_(False),
    )
    if address_id is not None:
        query = query.filter(Address.id != address_id)
    updated = query.update(
        {Address.is_default: False}, synchronize_session=False
    )
    db.commit()
    return updated


def unset_default_addresses(db: Session, user_id: int) -> int:
    """Clear ``is_default`` on every default address owned by *user_id*.

    Bulk UPDATE without an implicit commit, so callers can keep promoting the
    replacement default inside the same transaction.
    """
    return (
        db.query(Address)
        .filter(Address.user_id == user_id, Address.is_default == True)  # noqa: E712
        .update({"is_default": False})
    )


def create_address(
    db: Session,
    *,
    user_id: int,
    full_name: str,
    address_line1: str,
    city: str,
    state: Optional[str] = None,
    postal_code: Optional[str] = None,
    country: str = "US",
    is_default: bool = False,
    label: Optional[str] = None,
    phone: Optional[str] = None,
) -> Address:
    """Persist a new customer address and return the saved row."""
    country_code = (country or "US").upper()
    address = Address(
        user_id=user_id,
        full_name=full_name,
        address_line1=address_line1,
        city=city,
        state=state,
        postal_code=postal_code,
        country=country,
        country_code=country_code,
        is_default=bool(is_default),
        label=label,
        phone=phone,
    )
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


def update_address(db: Session, address: Address, updates: dict) -> Address:
    """Apply *updates* to an existing address row and persist them."""
    for key, value in (updates or {}).items():
        if key == "street":
            key = "address_line1"
        if key == "country":
            setattr(address, "country", value)
            setattr(address, "country_code", (value or "US").upper())
            continue
        if hasattr(address, key):
            setattr(address, key, value)
    db.commit()
    db.refresh(address)
    return address


def delete_address(db: Session, address: Address) -> None:
    """Hard-delete an address row."""
    db.delete(address)
    db.commit()


def set_default_address(db: Session, address: Address) -> Address:
    """Mark *address* as the user's default address and persist it."""
    address.is_default = True
    db.commit()
    db.refresh(address)
    return address


# Lazy re-exports for helpers that legitimately live in other modules. Kept out
# of the module globals so importing this file never triggers their load-time
# dependency graph (which caused circular imports during the earlier refactor).
_REEXPORTS: dict[str, tuple[str, str]] = {
    "clear_wishlist": ("services.commerce.wishlist_write_service", "clear_wishlist"),
    "create_wishlist_item": ("services.commerce.wishlist_write_service", "create_wishlist_item"),
    "delete_wishlist_item": ("services.commerce.wishlist_write_service", "delete_wishlist_item"),
    "create_review": ("controllers.commerce.reviews_controller", "create_review"),
    "update_review": ("controllers.commerce.reviews_controller", "update_review"),
    "delete_review": ("controllers.commerce.reviews_controller", "delete_review"),
    "soft_delete_review": ("services.commerce.reviews_service", "soft_delete_review"),
}


def __getattr__(name: str):
    spec = _REEXPORTS.get(name)
    if spec is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(spec[0])
    value = getattr(module, spec[1])
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(_REEXPORTS))
