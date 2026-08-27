"""Canonical address service — single source of truth for address operations."""
from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from domains.accounts.models.core import Address
from infrastructure.utils.pagination import SAFE_QUERY_LIMIT


def _normalize_address_payload(payload: dict, *, partial: bool = False) -> dict:
    street = payload.get("street", payload.get("address_line1"))
    state = payload.get("state", payload.get("region"))
    postal_code = payload.get("postal_code", payload.get("zip"))
    normalized = {
        "label": payload.get("label"),
        "street": street,
        "city": payload.get("city"),
        "state": state,
        "postal_code": postal_code,
        "country": payload.get("country"),
        "is_default": payload.get("is_default"),
    }
    if partial:
        return {key: value for key, value in normalized.items() if value is not None}
    required = {"street": street, "city": payload.get("city"), "country": payload.get("country")}
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Missing required fields: {', '.join(missing)}")
    return normalized


def _serialize_address(address: Address) -> dict:
    return {
        "id": address.id,
        "user_id": address.user_id,
        "label": getattr(address, "label", None),
        "street": address.address_line1,
        "address_line1": address.address_line1,
        "address_line2": address.address_line2,
        "city": address.city,
        "state": address.state,
        "postal_code": address.postal_code,
        "country": address.country,
        "is_default": address.is_default,
        "full_name": address.full_name,
        "phone": address.phone,
        "created_at": address.created_at,
    }


def list_user_addresses(db: Session, user_id: int, limit: int = SAFE_QUERY_LIMIT, cursor: int | None = None) -> list:
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


def unset_other_default_addresses(
    db: Session, user_id: int, address_id: Optional[int] = None
) -> int:
    query = db.query(Address).filter(
        Address.user_id == user_id,
        Address.is_default.is_(True),
    )
    if address_id is not None:
        query = query.filter(Address.id != address_id)
    updated = query.update(
        {Address.is_default: False}, synchronize_session=False
    )
    db.commit()
    return updated


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
    allowed_fields = {"full_name", "address_line1", "address_line2", "city", "state", "postal_code", "country", "country_code", "is_default", "label", "phone"}
    for key, value in (updates or {}).items():
        if key == "street":
            key = "address_line1"
        if key == "country":
            setattr(address, "country", value)
            setattr(address, "country_code", (value or "US").upper())
            continue
        if key in allowed_fields:
            setattr(address, key, value)
    db.commit()
    db.refresh(address)
    return address


def delete_address(db: Session, address: Address) -> None:
    db.delete(address)
    db.commit()


def set_default_address(db: Session, address: Address) -> Address:
    address.is_default = True
    db.commit()
    db.refresh(address)
    return address


# ── Composite operations for thin routers ──────────────────────────────────

def list_addresses(db: Session, user_id: int, limit: int = 100, offset: int = 0) -> list:
    rows = list_user_addresses(db, user_id, limit, offset)
    return [_serialize_address(row) for row in rows]


def create_address_from_payload(db: Session, payload: dict, user_id: int) -> dict:
    normalized = _normalize_address_payload(payload)
    if normalized.get("is_default"):
        unset_other_default_addresses(db, user_id)
    address_data = {
        "user_id": user_id,
        "full_name": "Customer",
        "address_line1": normalized.get("street", ""),
        "city": normalized.get("city", ""),
        "state": normalized.get("state"),
        "postal_code": normalized.get("postal_code"),
        "country": normalized.get("country", "US"),
        "is_default": normalized.get("is_default", False),
    }
    if normalized.get("label"):
        address_data["label"] = normalized["label"]
    if normalized.get("phone"):
        address_data["phone"] = normalized["phone"]
    address = create_address(db, **address_data)
    return _serialize_address(address)


def update_address_from_payload(db: Session, address_id: int, payload: dict, user_id: int) -> dict:
    address = get_user_address(db, address_id, user_id)
    updates = _normalize_address_payload(payload, partial=True)
    if updates.get("is_default") is True:
        unset_other_default_addresses(db, user_id, address_id)
    if "street" in updates:
        updates.pop("street")
    address = update_address(db, address, updates)
    return _serialize_address(address)


def delete_address_by_id(db: Session, address_id: int, user_id: int) -> dict:
    address = get_user_address(db, address_id, user_id)
    delete_address(db, address)
    return {"detail": "Deleted"}


def set_default_address_by_id(db: Session, address_id: int, user_id: int) -> dict:
    unset_other_default_addresses(db, user_id, address_id)
    address = get_user_address(db, address_id, user_id)
    address = set_default_address(db, address)
    return _serialize_address(address)
