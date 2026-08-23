"""Read operations for customer addresses.

Extracted from routers/addresses.py so the routers layer no longer performs
direct DB access (W1 layering: routers -> services).
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from domains.accounts.models.core import Address
from infrastructure.utils.pagination import SAFE_QUERY_LIMIT


def list_user_addresses(db: Session, user_id: int, limit: int = SAFE_QUERY_LIMIT, cursor: int | None = None) -> list:
    """Keyset (cursor) pagination over a user's addresses, default-first then newest."""
    query = (
        db.query(Address)
        .filter(Address.user_id == int(user_id))
        .order_by(Address.is_default.desc(), Address.created_at.asc())
    )
    if cursor is not None:
        query = query.filter(Address.id < int(cursor))
    return query.limit(min(max(1, limit), SAFE_QUERY_LIMIT)).all()


def get_user_address(db: Session, address_id: int, user_id: int) -> Address:
    address = (
        db.query(Address)
        .filter(Address.id == address_id, Address.user_id == user_id)
        .first()
    )
    if address is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found.")
    return address
