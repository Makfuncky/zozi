"""Accounts — Address Service.

Self-contained address book management for user accounts.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from domains.governance.models.core import Address
import structlog

logger = structlog.get_logger(__name__)


# ── Internal helpers ───────────────────────────────────────────────────────────

def _serialize_address(addr: Address) -> dict:
    return {
        "id": addr.id,
        "user_id": addr.user_id,
        "label": getattr(addr, "label", None),
        "street": getattr(addr, "street", None) or getattr(addr, "address_line1", None),
        "city": getattr(addr, "city", None),
        "state": getattr(addr, "state", None),
        "postal_code": getattr(addr, "postal_code", None),
        "country": getattr(addr, "country", None),
        "is_default": getattr(addr, "is_default", False),
        "phone": getattr(addr, "phone", None),
        "full_name": getattr(addr, "full_name", None),
        "created_at": addr.created_at.isoformat() if addr.created_at else None,
        "updated_at": addr.updated_at.isoformat() if addr.updated_at else None,
    }


def _normalize_address_payload(payload: dict, *, partial: bool = False) -> dict:
    street = payload.get("street", payload.get("address_line1"))
    state = payload.get("state", payload.get("region"))
    normalized = {
        "label": payload.get("label"),
        "street": street,
        "city": payload.get("city"),
        "state": state,
        "postal_code": payload.get("postal_code", payload.get("zip")),
        "country": payload.get("country"),
        "is_default": payload.get("is_default"),
        "phone": payload.get("phone"),
        "full_name": payload.get("full_name"),
    }
    if partial:
        return {k: v for k, v in normalized.items() if v is not None}
    return normalized


def _get_own_address(address_id: int, user_id: int, db: Session) -> Address:
    addr = db.query(Address).filter(Address.id == address_id, Address.user_id == user_id).first()
    if not addr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found.")
    return addr


def unset_other_default_addresses(db: Session, user_id: int, except_id: int | None = None) -> None:
    """Clear the default flag on all addresses except the given one."""
    q = db.query(Address).filter(Address.user_id == user_id, Address.is_default.is_(True))
    if except_id is not None:
        q = q.filter(Address.id != except_id)
    q.update({"is_default": False})


# ── Public API ─────────────────────────────────────────────────────────────────

def list_addresses(db: Session, user_id: int, limit: int = 100, offset: int = 0) -> List[dict]:
    """List addresses for a user."""
    rows = (
        db.query(Address)
        .filter(Address.user_id == user_id)
        .order_by(Address.is_default.desc(), Address.created_at.asc())
        .offset(max(0, offset))
        .limit(min(max(1, limit), 100))
        .all()
    )
    return [_serialize_address(row) for row in rows]


def get_address(db: Session, address_id: int, user_id: int) -> dict:
    """Get a single address by ID."""
    addr = _get_own_address(address_id, user_id, db)
    return _serialize_address(addr)


def create_address(db: Session, user_id: int, **address_data) -> Address:
    """Create a new address for a user."""
    if address_data.get("is_default"):
        unset_other_default_addresses(db, user_id)
    addr = Address(user_id=user_id, **address_data)
    db.add(addr)
    db.commit()
    db.refresh(addr)
    return addr


def update_address(db: Session, address: Address, updates: dict) -> Address:
    """Update an existing address."""
    if updates.get("is_default") is True:
        unset_other_default_addresses(db, address.user_id, except_id=address.id)
    for field, value in updates.items():
        setattr(address, field, value)
    db.commit()
    db.refresh(address)
    return address


def delete_address(db: Session, address: Address) -> None:
    """Delete an address."""
    db.delete(address)
    db.commit()


def set_default_address(db: Session, address: Address) -> Address:
    """Set an address as the default."""
    unset_other_default_addresses(db, address.user_id, except_id=address.id)
    address.is_default = True
    db.commit()
    db.refresh(address)
    return address
