"""Address routes with compatibility for the recovered customer address contract."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from data.dependencies_auth import get_current_user
from data.db import get_db
from data.models import Address
from services.commerce_write_service import (
    create_address as create_address_db,
    update_address as update_address_db,
    delete_address as delete_address_db,
    unset_other_default_addresses,
    set_default_address as set_default_address_db,
)
from utils.pagination import cursor_paginate_asc, build_cursor_pagination_payload

router = APIRouter()


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


def _get_user_address(address_id: int, user_id: int, db: Session) -> Address:
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == user_id).first()
    if address is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found.")
    return address


@router.get("")
def list_addresses(limit: int = 100, offset: int = 0, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Address)
        .filter(Address.user_id == int(current_user["id"]))
        .order_by(Address.is_default.desc(), Address.created_at.asc())
        .offset(max(0, offset))
        .limit(min(max(1, limit), 100))
        .all()
    )
    return [_serialize_address(row) for row in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_address(payload: dict, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    normalized = _normalize_address_payload(payload)
    user_id = int(current_user["id"])
    if normalized.get("is_default"):
        unset_other_default_addresses(db, user_id)
    address = Address(
        user_id=user_id,
        full_name="Customer",
        address_line1=normalized.get("street", ""),
        city=normalized.get("city", ""),
        state=normalized.get("state"),
        postal_code=normalized.get("postal_code"),
        country=normalized.get("country", "US"),
        is_default=normalized.get("is_default", False),
    )
    if normalized.get("label"):
        address.label = normalized["label"]
    if normalized.get("phone"):
        address.phone = normalized["phone"]
    return _serialize_address(create_address_db(db, **{
        "user_id": user_id,
        "full_name": "Customer",
        "address_line1": normalized.get("street", ""),
        "city": normalized.get("city", ""),
        "state": normalized.get("state"),
        "postal_code": normalized.get("postal_code"),
        "country": normalized.get("country", "US"),
        "is_default": normalized.get("is_default", False),
        "label": normalized.get("label"),
        "phone": normalized.get("phone"),
    }))


@router.put("/{address_id}")
def update_address(address_id: int, payload: dict, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    address = _get_user_address(address_id, int(current_user["id"]), db)
    updates = _normalize_address_payload(payload, partial=True)
    if updates.get("is_default") is True:
        unset_other_default_addresses(db, address.user_id, address_id)
    if "street" in updates:
        address.address_line1 = updates.pop("street")
    return _serialize_address(update_address_db(db, address, updates))


@router.delete("/{address_id}")
def delete_address(address_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    address = _get_user_address(address_id, int(current_user["id"]), db)
    delete_address_db(db, address)
    return {"detail": "Deleted"}


@router.post("/{address_id}/set-default")
def set_default_address(address_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = int(current_user["id"])
    unset_other_default_addresses(db, user_id, address_id)
    address = _get_user_address(address_id, user_id, db)
    return _serialize_address(set_default_address_db(db, address))