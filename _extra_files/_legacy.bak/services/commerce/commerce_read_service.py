"""Read operations for customer addresses.

Extracted from routers/addresses.py so the routers layer no longer performs
direct DB access (W1 layering: routers -> services).
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from _legacy.models import Address


def list_user_addresses(db: Session, user_id: int, limit: int = 100, offset: int = 0) -> list:
    return (
        db.query(Address)
        .filter(Address.user_id == int(user_id))
        .order_by(Address.is_default.desc(), Address.created_at.asc())
        .offset(max(0, offset))
        .limit(min(max(1, limit), 100))
        .all()
    )


def get_user_address(db: Session, address_id: int, user_id: int) -> Address:
    address = (
        db.query(Address)
        .filter(Address.id == address_id, Address.user_id == user_id)
        .first()
    )
    if address is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found.")
    return address
